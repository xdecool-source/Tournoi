// Récupère la configuration des tableaux depuis le serveur.

export async function loadTableaux(){
    const r = await fetch("/tableaux");
    const data = await r.json();
    return data.tableaux || data;
}