// Vérifie les données (joueur, email, sélection)
// envoie l’inscription au serveur (création ou modification)
// gère les erreurs/tableaux pleins
// puis affiche un récapitulatif.

//  Send  Inscription 

import { currentPlayer, emailVerified, places, isAdmin } from "./state.js";
import { showRecap } from "./recap.js"

window.sendInscription = sendInscription;
export async function sendInscription(){
    // alert("CLICK DETECTED"); // on regarde si on rentre dans cette fonction
    if(!currentPlayer){
        alert("Licence non chargée");
        return;
    }
    if(!currentPlayer || !currentPlayer.fftt){
        return;
        }
    if(!emailVerified && !isAdmin){
        alert("Veuillez vérifier votre email avant de continuer");
        return;
    }
    const email = document.getElementById("email").value.trim();
    const error = document.getElementById("emailError");
    error.innerText = "";

    if(!email.includes("@")){
        error.innerText = "Saisie Mail invalide";
        return;
    }
    const selection = Array.from(
        document.querySelectorAll("#tableauxContainer input:checked")
    ).map(cb => cb.value);
    if(!currentPlayer){
        alert("Licence non chargée");
        return;
    }    
    // blocage tableau plein

    for(const t of selection){
        const p = places[t];

        // xxxx const p = places[t].capacite

        if(!p) continue;

        // FULL uniquement si capacite + attente saturées

        if(p.ok>= p.capacite && p.attente >= p.attente_max){

        // info visuelle mais on laisse backend décider

            console.log("FULL FRONT", t);
        }
    // sinon attente autorisée
    }
    const payload = {
        licence: currentPlayer.licence,
        nom: currentPlayer.nom,
        prenom: currentPlayer.prenom,
        club: currentPlayer.club,
        points: currentPlayer.points,
        mail: email,
        tableaux: selection
    };
    const method = currentPlayer.already_inscrit ? "PUT" : "POST";
    const url = currentPlayer.already_inscrit
        ? `/inscription/${currentPlayer.licence}`
        : "/inscription";

    //  anti double clic bouton

    const btn = document.querySelector("button[onclick='sendInscription()']");
    if(btn){
        btn.disabled = true;
        btn.innerText = "Enregistrement...";
    }
    const res = await fetch(url,{
        method,
        credentials: "include",   // cookies
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload)
    });

    if(res.status === 401){
        openModal("Session admin expirée");
        return;
    }

    let data;
    try{
        data = await res.json();
    }catch{
        openModal("Erreur serveur");
        return;
    }
    // récupérer la réponse backend
    // const data = await res.json();
    // réactivation bouton

    if(btn){
        btn.disabled = false;
        btn.innerText = currentPlayer.already_inscrit
            ? "Modifier inscription"
            : "Valider";
    }
    // gestion erreur backend

    if(data.success === false){
        openModal(data.error || "Erreur");
        return;
    }
    // ICI → tableaux refusés

    if(data.refused && data.refused.length){
        openModal(
            "Inscription validée mais tableaux pleins : " +
            data.refused.join(", ")
        );
    }
    closeModal();

    //  filtrer tableaux refusés backend
    
    const validSelection = data.refused?.length
        ? selection.filter(t => !data.refused.includes(t))
        : selection;
    console.log("SELECTION:", selection);
    console.log("REFUSED:", data.refused);
    console.log("VALID:", validSelection);
await showRecap(currentPlayer, email, validSelection);
}
