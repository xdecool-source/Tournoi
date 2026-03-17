// Affiche ou masque une fenêtre pop-up 
// avec un message d’erreur ou d’information.

// ---------- MODAL ----------
export function openModal(msg){

    document.getElementById("modalMsg").innerText = msg;
    document.getElementById("errorModal").classList.remove("hidden");
}

export function closeModal(){
    document.getElementById("errorModal").classList.add("hidden");
}