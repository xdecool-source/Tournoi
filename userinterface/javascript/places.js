// ---------- LOAD PLACES ----------
import { places } from "./state.js";

let placesEtag = null;
export async function loadPlaces(){

    try{
        const r = await fetch("/places",{
            headers: placesEtag ? {"If-None-Match": placesEtag} : {}
        });
        if(r.status === 304) return false;
        placesEtag = r.headers.get("ETag");
        const data = await r.json();
        Object.assign(places, data.places || data);
        return true;
    }catch(e){
        console.error("loadPlaces error", e);
        return false;

    }
}
