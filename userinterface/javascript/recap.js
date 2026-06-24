// Construit et affiche un résumé final de l’inscription 
// (joueur, email, tableaux, places restantes).

function escapeHTML(str){
    return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

export async function showRecap(player, email, tableauxSel){

    //  0 sécurité

    if(!player){
        // console.error("PLAYER UNDEFINED");
        return;
    }

    // 1 cacher les autres cartes

    document.getElementById("licenceCard")?.classList.add("hidden");
    document.getElementById("inscriptionCard")?.classList.add("hidden");

    const row = document.getElementById("inscriptionRow");
    if(row){
        row.style.display = "block";
    }

    // 2 reload config et places temps réel

    const conf = await fetch("/tableaux").then(r => r.json());
    const { helloasso_carte: helloassoCarte } =
        await fetch("/config").then(r => r.json());
    console.log("helloassoCarte =", helloassoCarte);
    const placesNow = await fetch("/places").then(r => r.json());

    let tableauxHTML = "";
    let total = 0; 

    tableauxSel.forEach(t=>{
        const c = conf[t];
        if(!c){
            return;
        }
        const p = placesNow[t] || {};
        // xx const jourTxt = c.jour === 1 ? "Samedi" : "Dimanche"; 
        const jourTxt = c.jour?.label || "Jour inconnu";
        const heureTxt = c.jour?.hour || "";

        if(!c){
            // console.warn("MANQUANT", t);
            return;
        }

        // const prix = Number(c.prix || 0);
        const prix = Number(c.prix ?? 0);
        total += prix;

        const restantes = Math.max(0, (p.capacite || 0) - (p.ok || 0));

        const range = (c.min != null && c.max != null)
            ? ` (${c.min}-${c.max} pts)`
            : "";

        let txt = "";
        let color = "green";

        if(p.ok >= p.capacite && p.attente >= p.attente_max){
            txt = `${p.capacite}/${p.capacite} et vous êtes le dernier en liste d'attente de ${p.attente_max} `;
            color = "red";
        }
        else if(p.ok >= p.capacite){
            txt = `${p.capacite}/${p.capacite} et vous êtes le (${p.attente}/${p.attente_max}) en liste d'attente`;
            color = "orange";
        }
        else{
            txt = `${restantes} places restantes`;
        }

        tableauxHTML += `
            <div style="
                margin-bottom:18px;
                padding:10px;
                background:#f8f8f8;
                border-radius:8px;
            ">

                <div style="margin-bottom:4px;">
                    <b>${escapeHTML(t)}</b>
                    ${escapeHTML(range)}
                    ${escapeHTML(jourTxt)} à ${escapeHTML(heureTxt)}
                    - 💰 <b>${prix}€</b>
                </div>

                <div style="color:${color}; font-weight:bold;">
                    ${escapeHTML(txt)}
                </div>

            </div>
        `;
    });

    // 3 contenu recap

    const recapContent = document.getElementById("recapContent");

    if(recapContent){
        recapContent.classList.remove("hidden");
        recapContent.style.display = "block"; 

        // console.log("TOTAL TOTAL =", total, typeof total);

        if(total === 0){

            recapContent.innerHTML = `
                <b style="color:red; font-size:20px;">
                    ❌ Annulation Inscription
                </b>
                <br><br>

                <b>${escapeHTML(player.prenom)} ${escapeHTML(player.nom)}</b><br>
                N° de Licence: <b>${escapeHTML(player.licence)}</b><br>
                Licencié au Club: ${escapeHTML(player.club)}<br>
                Ayant ${escapeHTML(player.points)} Points dans cette Phase<br>
                Votre Adresse Mail: ${escapeHTML(email)}<br><br>
                Plus aucun tableau sélectionné
                <br>
                <b style="color:#007bff;">
                    Un mail va suivre afin de confirmer votre annulation
                </b>
            `;

        }else{

            recapContent.innerHTML = `
                <b>${escapeHTML(player.prenom)} ${escapeHTML(player.nom)}</b><br>
                N° de Licence: <b>${escapeHTML(player.licence)}</b><br>
                Licencié au Club: ${escapeHTML(player.club)}<br>
                Ayant ${escapeHTML(player.points)} Points dans cette Phase<br>
                Votre Adresse Mail: ${escapeHTML(email)}<br><br>

                <b>Liste des tableaux validés</b><br><br>
                ${tableauxHTML}

                <b style="font-size:18px; color:#28a745;">
                    Total : ${total}€
                </b>
                <br><br>

                ${helloassoCarte ? `
                    <b style="color:#007bff;">
                        Votre inscription sera confirmée après validation du paiement.
                        <br>
                        Le paiement s'ouvrira dans un nouvel onglet HelloAsso.
                    </b>
                    <br><br>

                    <button
                        id="btnHelloAsso"
                        style="
                            background:#ffcc00;
                            color:black;
                            border:none;
                            padding:6px 12px;
                            border-radius:5px;
                            cursor:pointer;
                            font-weight:bold;
                            font-size:13px;
                        "
                    >
                        💳 Payer
                    </button>
                ` : `
                    <b style="color:#28a745;">
                        Votre inscription est enregistrée.
                        <br>
                        Vous recevrez un email de confirmation.
                    </b>
                `}
            `;

           
            if (helloassoCarte) {

                const btnHelloAsso = document.getElementById("btnHelloAsso");
                if (btnHelloAsso && window.helloassoPaymentUrl) {
                    btnHelloAsso.onclick = () => {
                        btnHelloAsso.outerHTML = `
                            <b style="color:#28a745;">
                                ✓ Fenêtre de paiement ouverte
                            </b>
                        `;
                        window.open(
                            window.helloassoPaymentUrl,
                            "_blank",
                            "noopener,noreferrer"
                        );
                    };
                }

            }
        }
    }

    // 4 afficher recap (FIX COMPLET)
    
    const recapCard = document.getElementById("recapCard");

    if(recapCard){
        recapCard.classList.remove("hidden");
        recapCard.style.display = "block";
        recapCard.style.width = "100%";
        recapCard.style.height = "auto";
        recapCard.style.overflow = "visible";
        recapCard.scrollIntoView({ behavior: "smooth" }); 
    }

}