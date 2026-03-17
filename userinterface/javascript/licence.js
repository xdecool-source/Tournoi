// Appelle le serveur pour valider une licence 
// Renvoie les infos du joueur ou une erreur si elle n’existe pas.

// ---------- CHECK LICENCE ----------
export async function checkLicence(lic){

    const r = await fetch("/licence/" + lic);
    if(!r.ok){
        const text = await r.text();
        try{
            const err = JSON.parse(text);
            throw new Error(err.detail || "Licence inexistante");
        }catch{
            throw new Error("Licence inexistante");
        }
    }
    return await r.json();
}
