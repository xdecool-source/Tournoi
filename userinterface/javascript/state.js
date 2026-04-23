// Stocke et Mise a jour des données globales 
// (joueur, points, email, places, admin).

export let currentPlayer = null;
export let joueurPoints = null;
export let emailVerified = false;
export let places = {};
export let isAdmin = false;

export function setCurrentPlayer(v){
    currentPlayer = v;
}

export function setJoueurPoints(v){
    joueurPoints = v;
}

export function setEmailVerified(v){
    emailVerified = v;
}

export function setIsAdmin(v){
    isAdmin = v;
}