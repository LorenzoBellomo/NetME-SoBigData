// ng serve - local - insecure
export const environment = {
  firebase: {
    projectId: 'netme-webapp',
    appId: '1:717511105162:web:3bf9d11391e1056b65ab73',
    storageBucket: 'netme-webapp.appspot.com',
    databaseURL: 'https://netme-webapp-default-rtdb.europe-west1.firebasedatabase.app',
    apiKey: 'AIzaSyDn7bpKGJCcJk2tpWFP-pIsSHJoROlvRZ4',
    authDomain: 'netme-webapp.firebaseapp.com',
    messagingSenderId: '717511105162',
    measurementId: 'G-GFVYK4814L',
  },
  production: false,
  apiURL: 'http://api.localhost:8092',
  wsURL: 'ws://api.localhost:8092',
};
