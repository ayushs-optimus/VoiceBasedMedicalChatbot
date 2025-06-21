// msalConfig.ts
import { Configuration } from '@azure/msal-browser';

export const msalConfig: Configuration = {
  auth: {
    clientId: 'c31016d8-fb79-4d1e-9dd9-158a71f8a8ad', // Replace with your Azure AD App's clientId
    authority: 'https://login.microsoftonline.com/b5db11ac-8f37-4109-a146-5d7a302f5881',
    redirectUri: 'https://containermedchat-react-frontend.icydesert-5434ff3f.canadacentral.azurecontainerapps.io/',
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};
