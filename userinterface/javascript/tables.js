// Récupère la configuration des tableaux depuis le serveur.

export async function loadTableaux(){

    const r = await fetch("/tableaux");
    if(!r.ok){
        throw new Error("Erreur serveur");
    }
    const data = await r.json();
    return data.tableaux || data;
}