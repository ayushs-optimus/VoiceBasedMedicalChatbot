import base64
import aiohttp
import jwt  # PyJWT
from jwt import ExpiredSignatureError, InvalidAudienceError, InvalidIssuerError, InvalidTokenError, PyJWTError
from fastapi import HTTPException
from app.config import get_settings
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from base64 import urlsafe_b64decode
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_random_exponential
import logging
import datetime

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

    def __str__(self) -> str:
        return self.error or ""


class AzureADAuth:
    def __init__(self):
        settings = get_settings()
        self.tenant_id = "b5db11ac-8f37-4109-a146-5d7a302f5881"
        self.client_id = "f47e1e9b-304b-4a4a-90a1-87bf0e29272b"
        self.key_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        self.valid_issuers = [
            f"https://login.microsoftonline.com/{self.tenant_id}/v2.0",
            f"https://sts.windows.net/{self.tenant_id}/"
        ]
        self.valid_audiences = [
             "00000003-0000-0000-c000-000000000000"
        ]
        self._jwks_cache = None
        self._jwks_last_updated = None
        logger.info(f"AzureADAuth initialized for Tenant ID: {self.tenant_id}, Client ID: {self.client_id}")
        logger.info(f"Valid Issuers: {self.valid_issuers}")
        logger.info(f"Valid Audiences: {self.valid_audiences}")


    async def get_jwks(self):
        cache_duration = datetime.timedelta(hours=24)

        if self._jwks_cache and (datetime.datetime.now() - self._jwks_last_updated < cache_duration):
            logger.info("Using cached JWKS.")
            return self._jwks_cache

        logger.info("Fetching new JWKS from Azure AD.")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.key_url) as response:
                    response.raise_for_status()
                    jwks_data = await response.json()
                    self._jwks_cache = jwks_data
                    self._jwks_last_updated = datetime.datetime.now()
                    logger.info(f"Successfully fetched JWKS. Contains {len(jwks_data.get('keys', []))} keys.")
                    return jwks_data
            except aiohttp.ClientError as e:
                logger.error(f"Failed to fetch Azure AD public keys from {self.key_url}: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch Azure AD public keys")

    def _pad_base64_string(self, b64_string: str) -> str:
        padding_needed = len(b64_string) % 4
        if padding_needed != 0:
            b64_string += '=' * (4 - padding_needed)
        return b64_string

    async def create_rsa_key(self, jwks: dict, token: str):
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            alg = unverified_header.get("alg")

            logger.info(f"Token Header - kid: {kid}, alg: {alg}")

            if not kid:
                logger.warning("JWT header is missing 'kid'. Cannot determine which key to use. This is unusual for Azure AD.")
                return None
            if alg and alg != "RS256":
                logger.warning(f"JWT algorithm '{alg}' is not RS256. This might be an issue for signature verification.")

            for key in jwks["keys"]:
                if key.get("kid") == kid:
                    logger.info(f"Found matching key in JWKS for kid: {kid}. Key type: {key.get('kty')}")
                    if key.get('kty') != 'RSA':
                        logger.error(f"Key with kid {kid} is not an RSA key ({key.get('kty')}). Cannot create RSA public key.")
                        return None

                    raw_e = key["e"]
                    raw_n = key["n"]

                    padded_e = self._pad_base64_string(raw_e)
                    padded_n = self._pad_base64_string(raw_n)

                    # print(f"Original e: {raw_e}")
                    # print(f"Padded e: {padded_e}")
                    # print(f"Original n: {raw_n}")
                    # print(f"Padded n: {padded_n}")

                    try:
                        decoded_e_bytes = urlsafe_b64decode(padded_e)
                        decoded_n_bytes = urlsafe_b64decode(padded_n)
                        # print(f"Decoded e bytes (hex): {decoded_e_bytes.hex()}")
                        # print(f"Decoded n bytes (hex): {decoded_n_bytes.hex()}")

                        exponent = int.from_bytes(decoded_e_bytes, byteorder="big")
                        modulus = int.from_bytes(decoded_n_bytes, byteorder="big")
                        # print(f"Converted exponent (int): {exponent}")
                        # print(f"Converted modulus (int) first 20 digits: {str(modulus)[:20]}...") # Modulus is very long
                    except Exception as decode_error:
                        logger.error(f"Error during base64 decoding or int conversion: {decode_error}", exc_info=True)
                        return None # Fail early if decoding fails

                    public_numbers = rsa.RSAPublicNumbers(exponent, modulus)
                    rsa_public_key = public_numbers.public_key(backend=default_backend())

                    public_pem = rsa_public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    # print(f"Successfully created RSA public key for kid: {kid}")
                    # print("\n--- Generated RSA Public Key (PEM format) ---")
                    # print(public_pem.decode('utf-8'))
                    # print("-------------------------------------------\n")

                    return rsa_public_key
            logger.warning(f"No matching public key found in JWKS for kid: {kid}. Available kids: {[k.get('kid') for k in jwks.get('keys', []) if k.get('kid')]}")
        except Exception as e:
            logger.error(f"Error creating RSA key from JWKS for token with kid {kid}: {e}", exc_info=True)
        return None
        
    async def validate_access_token(self, token: str) -> dict:
        jwks = None
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(HTTPException),
            wait=wait_random_exponential(min=15, max=60),
            stop=stop_after_attempt(5),
            reraise=True
        ):
            with attempt:
                jwks = await self.get_jwks()

        if not jwks or "keys" not in jwks:
            raise AuthError("Unable to get keys to validate auth token (JWKS empty or invalid).", 401)

        try:
            unverified_header = jwt.get_unverified_header(token)
            
            # --- MODIFICATION START ---
            # Set verify_signature to False here to bypass signature validation
            decoded_token = jwt.decode(
                token,
                options={"verify_signature": False}, # <--- Bypass signature verification
                algorithms=["RS256"], # Still specify algorithms if you want to verify other claims, but it won't check sig
                audience=self.valid_audiences, # Let PyJWT check audience
                issuer=self.valid_issuers # Let PyJWT check issuer
            )
            # --- MODIFICATION END ---

            # The explicit checks below are now redundant if PyJWT handles them,
            # but can be kept for custom logging/error messages if desired.

            issuer = decoded_token.get("iss")
            audience = decoded_token.get("aud")

            logger.info(f"Decoded Claims (Signature Bypassed) - Issuer: {issuer}, Audience: {audience}")

            # You can keep these explicit checks if you want more control over error messages
            if issuer not in self.valid_issuers:
                logger.warning(f"Invalid issuer: '{issuer}'. Expected one of {self.valid_issuers}")
                raise AuthError(f"Issuer {issuer} not valid", 401)

            audience_is_valid = False
            if isinstance(audience, list):
                if any(aud in self.valid_audiences for aud in audience):
                    audience_is_valid = True
            elif audience in self.valid_audiences:
                audience_is_valid = True

            if not audience_is_valid:
                logger.error(f"Invalid audience: '{audience}'. Token's audience does not match any of the valid audiences: {self.valid_audiences}. This token is likely for another resource (e.g., Microsoft Graph).")
                raise InvalidAudienceError(f"Audience '{audience}' is not valid for this API. Expected one of: {self.valid_audiences}")

            # Note: If you bypass signature verification, you no longer need to call create_rsa_key
            # and pass the key to jwt.decode. The key=rsa_key line would be removed if you
            # are fully bypassing signature verification.

            logger.info("Token validated successfully (signature verification bypassed).")
            return decoded_token
        except ExpiredSignatureError as e:
            logger.error(f"Token is expired: {e}")
            raise AuthError("Token is expired", 401) from e
        except InvalidAudienceError as e:
            logger.error(f"Incorrect claims (audience invalid): {e}")
            raise AuthError(f"Incorrect claims: audience invalid - {e}", 401) from e
        except InvalidIssuerError as e:
            logger.error(f"Incorrect claims (issuer invalid): {e}")
            raise AuthError(f"Incorrect claims: issuer invalid - {e}", 401) from e
        except InvalidTokenError as e:
            logger.error(f"General token error (e.g., malformed token, but not signature if bypassed): {e}")
            raise AuthError("Invalid token format or other non-signature error", 401) from e
        except PyJWTError as e:
            logger.error(f"A PyJWT error occurred during validation: {e}")
            raise AuthError(f"Token validation failed due to PyJWT error: {e}", 401) from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during token validation: {e}", exc_info=True)
            raise AuthError(f"Token validation failed: {e}", 401) from e


def get_auth_client() -> AzureADAuth:
    return AzureADAuth()