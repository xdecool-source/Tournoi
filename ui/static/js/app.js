
// vérification de licence FFTT
// affichage des tableaux disponibles
// sélection des tableaux
// envoi de l’inscription au backend
// affichage du récapitulatif et gestion admin.

let tableaux = {};
let joueurPoints = null;
let currentPlayer = null;
let places = {};

// Frontend
// console.log("APP JS CHARGE");

const isAdmin = document.cookie.includes("admin=1");
let lastCheckedLicence = null;

console.log("APP LOADED")
if(isAdmin){
    document.getElementById("logoutBtn").style.display="block";
    document.querySelector("button[onclick='loginAdmin()']").style.display="none";
}

// ---------- LOAD PLACES ----------
let placesEtag = null;

async function loadPlaces(){
    try{
        const r = await fetch("/places", {
            headers: placesEtag ? {"If-None-Match": placesEtag} : {}
        });

        //  rien changé → stop
        if(r.status === 304) return false;

        placesEtag = r.headers.get("ETag");

        const data = await r.json();
        places = data.places || data;

        return true;

    }catch(e){
        console.error("loadPlaces error", e);
        places = {};
    }
}

// ---------- LOAD TABLEAUX ----------
async function loadTableaux(){
    const r = await fetch("/tableaux");
    const data = await r.json();
    TABLEAUX = data.tableaux || data;
}


// ---------- Rafraichissement pour les compteurs (4 secondes)
async function init(){
    await loadTableaux();
    await loadPlaces();
    renderTableaux();
    
    // FIX polling email et Tableaux
    // document.querySelector("#licence")?.focus();
    setInterval(async ()=>{

    // 🔴 1️⃣ Si on tape dans le champ licence → on ne refresh pas
    if(document.activeElement?.id === "licence") return;

    // 🔴 2️⃣ Si une case est cochée → on ne refresh pas
    if(document.querySelector("#tableauxContainer input:checked")) return;

    const changed = await loadPlaces();
    if(changed) renderTableaux();

    }, 10000);
}

init();

// saisir sur smartphone 
// saisie licence (compatible smartphone)
let licenceTimer = null;

document.getElementById("licence").addEventListener("keydown", e=>{
    if(e.key === "Enter"){
        check();
    }
});


document.querySelector("#licence").addEventListener("keydown", e=>{
    if(e.key === "Enter" || e.key === "NumpadEnter" || e.keyCode === 13){
        check();
    }
});

function resetInterface(){

    // reset variables
    currentPlayer = null;
    joueurPoints = null;

    // vider affichage joueur
    const res = document.getElementById("result");
    if(res) res.innerHTML = "";

    // vider email
    const mail = document.getElementById("email");
    if(mail) mail.value = "";

    // masquer message déjà inscrit
    const msg = document.getElementById("alreadyMsg");
    if(msg){
        msg.classList.add("hidden");
        msg.innerHTML = "";
    }

    // réactiver bouton inscription
    const btn = document.querySelector("button[onclick='sendInscription()']");
    if(btn){
        btn.disabled = false;
        btn.innerText = "Valider";
        btn.style.opacity = 1;
    }

    // décocher et réactiver tous les tableaux
    document.querySelectorAll("#tableauxContainer input").forEach(el=>{
        el.checked = false;
        el.disabled = false;
    });

    // masquer carte inscription
    const card = document.getElementById("inscriptionCard");
    if(card){
        card.style.display = "none";
        card.classList.add("hidden");
    }
}


function resetToStart(){

    document.getElementById("licence").value="";
    document.getElementById("email").value="";
    document.getElementById("result").innerHTML="";

    document.querySelectorAll("#tableauxContainer input").forEach(el=>{
        el.checked=false;
        el.disabled=false;
    });

    joueurPoints=null;
    currentPlayer=null;

    goToStep("licenceCard");

    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    },800);
}






function limitSelection(){
    const checked = document.querySelectorAll(
        "#tableauxContainer input:checked"
    );
    if(checked.length > 4){
        this.checked = false;
        openModal("Maximum 4 tableaux");
    }
}

// ------------ Comptage pour les tableaux ---------------------
// ------------ function renderTableaux(tableaux, places) ------

function renderTableaux(){

    // 🔹 Sauvegarde focus + position curseur
    const activeElement = document.activeElement;
    let cursorPosition = null;

    if(activeElement && activeElement.tagName === "INPUT"){
        cursorPosition = activeElement.selectionStart;
    }

    const checked = Array.from(
        document.querySelectorAll("#tableauxContainer input:checked")
    ).map(cb => cb.value);

    const box = document.getElementById("tableauxContainer");
    if(!box || !TABLEAUX) return;

    box.innerHTML = Object.keys(TABLEAUX).map(key => {

        const conf = TABLEAUX[key];
        if(!conf) return "";

        const used   = places?.[key]?.ok ?? 0;
        const cap    = places?.[key]?.capacite ?? conf.capacite ?? 0;
        const att    = places?.[key]?.attente ?? 0;
        const attMax = places?.[key]?.attente_max ?? conf.attente ?? 0;

        const min = conf.min ?? null;
        const max = conf.max ?? null;

        let interdit = false;

        if(joueurPoints !== null){
            if(min !== null && joueurPoints < min) interdit = true;
            if(max !== null && joueurPoints > max) interdit = true;
        }

        let disabledAttr = "";
        let color = "green";
        let badge = `${att}/${attMax}`;

        if(interdit){
            color = "grey";
            disabledAttr = "disabled";
            badge = `${att}/${attMax} ⛔️ Interdit`;
        }
        else if(used >= cap && att >= attMax){
            color = "red";
            disabledAttr = "disabled";
            badge = "🔒 COMPLET";
        }
        else if(used >= cap){
            color = "orange";
        }

        const isChecked =
            (checked.includes(key) && disabledAttr === "")
                ? "checked"
                : "";

        return `
        <div class="tableau-row ${color} ${interdit ? "tableau-interdit" : ""}">
            <input type="checkbox"
                value="${key}"
                ${disabledAttr}
                ${isChecked}
                onchange="limitSelection.call(this)">

            <span class="col-tableau">${key}</span>

            <span class="col-tranche ${interdit ? "tranche-ko" : "tranche-ok"}">
                ${min ?? "-"}-${max ?? "-"}
            </span>

           <div class="tableau-stats">

            <span class="stat-inscrit">
                🏓 Inscrit ${used}/${cap}
            </span>

            <span class="stat-attente">
                ⏳ Attente ${badge}
            </span>

            </div>
            
        </div>`;
        
    }).join("");

    /* force recalcul layout sur mobile */
    box.offsetHeight;
    // 🔹 Restauration focus + curseur
    if(activeElement && document.body.contains(activeElement)){
        activeElement.focus();
        if(cursorPosition !== null){
            activeElement.setSelectionRange(cursorPosition, cursorPosition);
        }
    }
}






// ---------- CHECK LICENCE ----------

let checkTimer = null;
async function check(){
    const input = document.getElementById("licence");
    if(!input) return;
    const lic = input.value.trim();
    if(!lic) return;
    clearTimeout(checkTimer);
    checkTimer = setTimeout(async ()=>{
        const isAdmin = document.cookie.includes("admin=1");
        if(!/^\d+$/.test(lic)){
            openModal("Licence numérique obligatoire");
            return;
        }

        try{
            const r = await fetch("/licence/" + lic);
            if(!r.ok){
                const text = await r.text();
                try{
                    const err = JSON.parse(text);
                    openModal(err.detail || "Licence inexistante");
                }catch{
                    openModal("Licence inexistante");
                }
                return;
            }
            const data = await r.json();
            currentPlayer = data;
            const errBox = document.getElementById("licenceError");
            // cacher message si licence valide
            if(errBox){
                errBox.classList.add("hidden");
            }
            if(!data.fftt){
                // message inline
                if(errBox){
                    errBox.innerText = "Licence inconnue FFTT";
                    errBox.classList.remove("hidden");
                }

                // masquer tableaux
                document.getElementById("tableauxContainer").innerHTML="";

                // masquer inscription
                const card = document.getElementById("inscriptionCard");
                if(card){
                    card.style.display="none";
                    card.classList.add("hidden");
                }

                return; // STOP ici
            }

            // 





            joueurPoints = data.points ? Number(data.points) : 9999;
            const res = document.getElementById("result");
            if(res){
                res.innerHTML = `
                    <b>${data.prenom||""} ${data.nom||""}</b><br>
                    Club: ${data.club||""}<br>
                    Points: ${data.points||""}`;
            }
            const card = document.getElementById("inscriptionCard");
            if(card){
                card.classList.remove("hidden");
                card.style.display="block";
            }

            const mailInput = document.getElementById("email");
            if(mailInput){
                mailInput.value = data.mail || "";

                // focus automatique email
                setTimeout(()=>{
                    mailInput.focus();
                },120);
            }
            await loadTableaux();
            await loadPlaces();
            renderTableaux();

            if(data.already_inscrit){
                const msg = document.getElementById("alreadyMsg");
            if (msg) {
                msg.classList.remove("hidden");
                msg.innerHTML = `
                    Vous êtes déjà inscrit.<br>
                    Pour modifier votre inscription<br>
                    merci d'envoyer un mail à <br>
                    <a href="mailto:thuirtt66@gmail.com" style="color:red; text-decoration:underline;">
                    thuirtt66@gmail.com
                    </a>
                `;
}
                data.tableaux_inscrits?.forEach(t=>{
                    const el = document.querySelector(`input[value="${t}"]`);
                    if(el){
                        el.checked = true;
                        if(!isAdmin) el.disabled = true;
                    }
                });
                const btn = document.querySelector("button[onclick='sendInscription()']");
                if(btn){
                    if(!isAdmin){
                        btn.disabled = true;
                        btn.innerText = "Déjà inscrit";
                        btn.style.opacity = 0.5;
                    }else{
                        btn.disabled = false;
                        btn.innerText = "Modifier inscription";
                        btn.style.opacity = 1;
                    }
                }
            }

            
        }catch(e){
            console.error("check error", e);
            openModal("Erreur serveur licence");
        }
    }, 250);
}

// ---------- SEND INSCRIPTION ----------
async function sendInscription(){

    if(!currentPlayer){
        alert("Licence non chargée");
        return;
    }
    if(!currentPlayer || !currentPlayer.fftt){
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
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(payload)
    });
    // récupérer la réponse backend
    const data = await res.json();
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


await showRecap(currentPlayer, email, validSelection);



}

// ---------- RECAP ----------
async function showRecap(player, email, tableauxSel){

    // 🔹 cacher les autres cartes
    document.getElementById("licenceCard")?.classList.add("hidden");
    document.getElementById("inscriptionCard")?.classList.add("hidden");

    // 🔹 reload config et places temps réel
    const confRaw = await fetch("/tableaux").then(r=>r.json());
    const conf = confRaw.tableaux || confRaw;   // ✅ correction structure

    const placesNow = await fetch("/places").then(r=>r.json());

    let tableauxHTML = "";

    tableauxSel.forEach(t=>{
        const c = conf[t];
        const p = placesNow[t];

        if(!c || !p) return;

        const restantes = Math.max(0, p.capacite - p.ok);

        const range = (c.min != null && c.max != null)
            ? ` (${c.min}-${c.max} pts)`
            : "";

        let txt = "";
        let color = "green";

        if(p.ok >= p.capacite && p.attente >= p.attente_max){
            txt = `${p.capacite}/${p.capacite} et vous êtes le dernier en liste d'attente`;
            color = "red";
        }
        else if(p.ok >= p.capacite){
            txt = `${p.capacite}/${p.capacite} Vous êtes le (${p.attente}/${p.attente_max}) en liste d'attente`;
            color = "orange";
        }
        else{
            txt = `${restantes} places restantes`;
            color = "green";
        }

        tableauxHTML += `
            <div style="margin:6px 0">
                <b>${t}</b>${range}
                <br>
                <span style="color:${color}">
                    ${txt}
                </span>
            </div>
        `;
    });

    // 🔹 contenu recap (structure conservée)
    document.getElementById("recapContent").classList.remove("hidden");
    document.getElementById("recapContent").innerHTML = `
        <b>${player.prenom} ${player.nom}</b><br>
        N° de Licence: ${player.licence}<br>
        Licencié au Club: ${player.club}<br>
        Ayant ${player.points} Points en Phase 2<br>
        Votre Adresse Mail: ${email}<br><br>
        ✌️Liste des tableaux validés<br>
        ${tableauxHTML}
        <br><br>
        <b style="color:#007bff;">
        Un mail vous sera envoyé pour confirmer votre inscription
        </b>
        <br><br>
            `;

    // 🔹 afficher recap
    document.getElementById("recapCard")?.classList.remove("hidden");
}


// ---------- MODAL ----------
function openModal(msg){
    document.getElementById("modalMsg").innerText = msg;
    document.getElementById("errorModal").classList.remove("hidden");
}

function closeModal(){
    document.getElementById("errorModal").classList.add("hidden");
}

async function refreshPlaces(){
    const res = await fetch("/places");
    const places = await res.json();

    renderTableaux(window.TABLEAUX, places);
}

async function loginAdmin(){
    const pwd = prompt("Mot de passe admin");
    if(!pwd) return;

    const res = await fetch("/login-admin",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({pwd})
    });

    const data = await res.json();

    if(data.success){

        // Met à jour les boutons sans reload
        const adminBtn = document.querySelector("button[onclick='loginAdmin()']");
        const logoutBtn = document.getElementById("logoutBtn");

        if(adminBtn) adminBtn.style.display="none";
        if(logoutBtn) logoutBtn.style.display="block";

        // Si une licence est déjà chargée → on recharge juste son état
        if(currentPlayer){
            await check();
        }

    }else{
        openModal("Mot de passe incorrect");
    }
    setTimeout(()=>{
    document.getElementById("licence")?.focus();
    }, 100);
}

async function logoutAdmin(){
    await fetch("/logout-admin",{method:"POST"});

    const adminBtn = document.querySelector("button[onclick='loginAdmin()']");
    const logoutBtn = document.getElementById("logoutBtn");

    if(adminBtn) adminBtn.style.display="block";
    if(logoutBtn) logoutBtn.style.display="none";

    resetToStart();

    setTimeout(()=>{
    document.getElementById("licence")?.focus();
    }, 100);
}





window.check = check;

window.addEventListener("load", ()=>{
    const isAdmin = document.cookie.includes("admin=1");
    const adminBtn = document.querySelector("button[onclick='loginAdmin()']");
    const logoutBtn = document.getElementById("logoutBtn");
    if(isAdmin){
        adminBtn.style.display="none";
        logoutBtn.style.display="block";
    }else{
        adminBtn.style.display="block";
        logoutBtn.style.display="none";
    }
});

window.addEventListener("load", ()=>{
    setTimeout(()=>{
        document.getElementById("licence")?.focus();
    }, 200);
});

document.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === "NumpadEnter" || e.keyCode === 13) {
        const input = document.querySelector("#licence");
        if (input && document.activeElement === input) {
            console.log("CHECK CALL");
            check();
        }
    }
});

window.limitSelection = limitSelection;

document.addEventListener("change", function(e){

if(e.target.matches('#tableauxContainer input[type="checkbox"]')){

const card = e.target.closest(".tableau-row");

if(e.target.checked){
card.classList.add("selected");
}else{
card.classList.remove("selected");
}

}

});
