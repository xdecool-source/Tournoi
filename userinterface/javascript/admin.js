// loginAdmin
// demande un mot de passe
// active le mode admin
// affiche le bouton logout
// recharge le joueur (check())
// affiche une erreur
// logoutAdmin()
// désactive le mode admin

import { resetInterface } from "./reset.js";
import { openModal } from "./modal.js";
import { currentPlayer } from "./state.js";

function updateAdminInterface(isAdmin){

    const adminBtn = document.getElementById("adminBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const excelBtn = document.getElementById("GenerateExcelBtn");
    const listeBtn = document.getElementById("btnListeInscrits");

    if(isAdmin){
        if(adminBtn){adminBtn.style.display = "none";}
        if(logoutBtn){logoutBtn.style.display = "block";}
        if(excelBtn){excelBtn.style.display = "block";}
        if(listeBtn){listeBtn.style.display = "block";}
    }else{
        if(adminBtn){adminBtn.style.display = "block";}
        if(logoutBtn){logoutBtn.style.display = "none";}
        if(excelBtn){excelBtn.style.display = "none";}
        if(listeBtn){listeBtn.style.display = "none";}
    }
}

export async function loginAdmin(){

    // console.log("LOGIN FRONT CALLED "); 
    const pwd = prompt("Mot de passe admin");
    if(!pwd) return;
    const res = await fetch("/login-admin",{
        method:"POST",
        credentials: "include",  
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({pwd})
    });

    const data = await res.json();
    if(data.success){
             updateAdminInterface(true);

            // await window.check(); 
            // juste rafraîchir l'affichage sans relancer tout
        if(currentPlayer){
            setTimeout(() => {
                window.check();   // Reload complet avec isAdmin
            }, 200);
        }
    }else{
        openModal("Mot de passe incorrect");
    }
    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    },100);
}

export async function logoutAdmin(){

    await fetch("/logout-admin",{
        method:"POST",
        credentials: "include" 
    });
    localStorage.removeItem("isAdmin"); 
    updateAdminInterface(false);
   
    resetInterface();
    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    },100);
}

export async function excelAdmin(){

    try {
        const res = await fetch("/admin/export", {
            method: "POST",
            credentials: "include"
        });
        if(!res.ok){
            const data = await res.json().catch(() => null);
            openModal(data?.detail || "Erreur lors de la génération du fichier Excel");
            return;
        }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const disposition = res.headers.get("Content-Disposition");
        let filename = "Inscriptions_Tournoi.xlsx";
        if(disposition){
            const match = disposition.match(
                /filename="?([^"]+)"?/
            );

            if(match && match[1]){
                filename = match[1];
            }
        }
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

    } catch(error) {
        console.error("Erreur export Excel :", error);
        openModal(
            "Impossible de générer le fichier Excel"
        );
    }
}

// Fonctions utilisées par les onclick du HTML
window.loginAdmin = loginAdmin;
window.logoutAdmin = logoutAdmin;
window.excelAdmin = excelAdmin;
