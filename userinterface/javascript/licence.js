// Appelle le serveur pour valider une licence 
// Renvoie les infos du joueur ou une erreur si elle n’existe pas.

//  Vérif Licence  

export async function checkLicence(lic){

    try{
        const r = await fetch("/licence/" + encodeURIComponent(lic));
        if(!r.ok){
            try{
                const err = await r.json();
                throw new Error(err.detail || "Licence inexistante");
            }catch{
                throw new Error("Licence inexistante");
            }
        }
        const data = await r.json();
        if(typeof data !== "object" || data === null){
            throw new Error("Réponse invalide");
        }
        return data;
    }catch(e){
        throw new Error(e.message || "Erreur réseau");
    }
}
