// Récupère depuis le serveur l’état des places disponibles (avec cache ETag) 
// Mise à jour les données côté client.
// ETAG = identifiant de version d’une ressource côté serveur
// evite le renvoi de données

//  Load Places   

import { places } from "./state.js";

let placesEtag = null;

export async function loadPlaces(){
    try{
        const r = await fetch("/places",{
            headers: placesEtag ? {"If-None-Match": placesEtag} : {}
        });
        if(r.status === 304) return false;
        if(!r.ok){
            throw new Error("Erreur serveur");
        }
        const etag = r.headers.get("ETag");
        if(etag) placesEtag = etag;
        const data = await r.json();
        if(typeof data !== "object" || data === null){
            return false;
        }
        Object.assign(places, data.places || data);
        return true;
    }catch(e){
        console.error("loadPlaces error", e);
        return false;
    }
}