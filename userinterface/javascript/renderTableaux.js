// Génère l’interface des tableaux
//  (avec règles, états, sélection limitée et visuel dynamique).



function escapeHTML(str){
    return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

//  Render Tableaux 

export function renderTableaux(
    TABLEAUX,
    places,
    joueurPoints,
    alreadyInscrit = false,
    tableauxInscrits = [],
    isAdmin = false  
){
    window.TABLEAUX_GLOBAL = TABLEAUX; 
    // const isAdmin = document.cookie.includes("admin=1");
    const box = document.getElementById("tableauxContainer");
    // console.log("IS ADMIN RENDER:", isAdmin);
    if(!box || !TABLEAUX) return;

    const points = Number(joueurPoints);

    box.innerHTML = Object.keys(TABLEAUX).map(key => {
    const conf = TABLEAUX[key];
    if(!conf) return "";

    const jourTxt = escapeHTML(conf.jour?.label || "Jour inconnu");
    const safeKey = escapeHTML(key);
    const safeLabel = escapeHTML(conf.label ?? "");
    const safePrix = Number(conf.prix ?? 0); // number safe

    const used   = places?.[key]?.ok ?? 0;
    const cap    = places?.[key]?.capacite ?? conf.capacite ?? 0;
    const att    = places?.[key]?.attente ?? 0;
    const attMax = places?.[key]?.attente_max ?? conf.attente ?? 0;

    const min = conf.min != null ? Number(conf.min) : null;
    const max = conf.max != null ? Number(conf.max) : null;

    const isChecked = tableauxInscrits.includes(key);

    let interdit = false;
    if(!isNaN(points)){
        if(min !== null && points < min) interdit = true;
        if(max !== null && points > max) interdit = true;
    }

    let color = "green";
    let disabled = false;
    let attenteLabel = `${att}/${attMax}`;

    if(interdit){
        color = "grey";
        attenteLabel = `${att}/${attMax} ⛔️`;
        disabled = true;
    }
    else if(att >= attMax){
        color = "red";
        attenteLabel = "🔒 COMPLET";
        disabled = true;
    }
    else if(used >= cap){
        color = "orange";
    }

    if(alreadyInscrit && !isAdmin){
        disabled = true;
        if(isChecked){
            attenteLabel = `${att}/${attMax} 🔒 Déjà inscrit`;
        }
    }

    if(isAdmin){
        disabled = false;
    }

    return `
    <div class="tableau-row ${color} ${isChecked ? "selected" : ""} ${interdit ? "tableau-interdit" : ""} ${alreadyInscrit && !isAdmin ? "locked" : ""}">
        <label class="checkbox-wrap">
            <input type="checkbox"
                value="${safeKey}"
                data-prix="${safePrix}"
                ${disabled ? "disabled" : ""}
                ${isChecked ? "checked" : ""}>
            <span class="checkmark"></span>
        </label>

        <div class="col-tableau">
            <div class="jour">${jourTxt}</div>
            <div class="tableau-ligne">
                ${safeKey} - 💰 ${safePrix}€
            </div>
        </div>
        
        <span class="col-tranche ${interdit ? "tranche-ko" : "tranche-ok"}">
            ${safeLabel || (min !== null && max !== null ? `${min}-${max}` : "")}
        </span>

        <div class="tableau-stats">
            <span>🏓 ${used}/${cap}</span>
            <span>⏳ ${att}/${attMax}</span>
        </div>
    </div>`;
}).join("");

// 👇 ICI (après le render complet)
box.querySelectorAll('input[type="checkbox"]').forEach(cb=>{
    cb.addEventListener("change", limitSelection);
});
}

export function limitSelection(e){

    const current = e.target;

    const checked = Array.from(
        document.querySelectorAll("#tableauxContainer input:checked")
    );

    const counts = {};
    const grouped = {};

    checked.forEach(cb => {
        const c = window.TABLEAUX_GLOBAL?.[cb.value];
        const jour = c?.jour?.label?.toLowerCase();

        if(!jour) return;

        counts[jour] = (counts[jour] || 0) + 1;

        if(!grouped[jour]) grouped[jour] = [];
        grouped[jour].push(cb);
    });

    for(const jour in counts){
        if(counts[jour] > 4){

            // ❗ on garde les 4 premiers, on décoche le reste
            const list = grouped[jour];

            list.slice(4).forEach(cb => {
                cb.checked = false;
            });

            openModal(`Maximum 4 tableaux le ${jour}`);
            return;
        }
    }
}


window.limitSelection = limitSelection;

// gestion visuelle sélection

document.addEventListener("change", function(e){

    if(!e.target.matches('#tableauxContainer input[type="checkbox"]')){
        return;
    }

    let total = 0;
    document.querySelectorAll(
        "#tableauxContainer input:checked"
    ).forEach(cb => {
        const prix = parseInt(cb.dataset.prix || "0", 10);
        total += isNaN(prix) ? 0 : prix;
    });
    const el = document.getElementById("totalPrix");
    if(el){
        el.innerText = "Total : " + total + "€";
    }
    // console.log("TOTAL =", total); 
});
