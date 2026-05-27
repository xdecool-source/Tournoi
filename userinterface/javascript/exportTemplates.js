export function createCard({
    titre,
    contenu,
    footer = "",
    color = "#1976d2"
}){

    return `
        <div class="card">
            <h2 style="color:${color}">
                ${contenu}
            </h2>
            <p>
                ${titre}
            </p>
            <small>
                ${footer}
            </small>
        </div>
    `;
}

export function createBadge(
    t,
    attente = false
){
    return `
    <span class="
        badge
        ${attente ? 'badge-attente' : ''}
    ">
        ${t}
            ${attente ? ' ATTENTE' : ''}
    </span>
    `;
}

export function createPlayerRow(p, badges){

    return `
        <tr>
            <td>${p.dossard}</td>
            <td>${p.licence}</td>
            <td>${p.nom}</td>
            <td>${p.prenom}</td>
            <td>${p.club}</td>
            <td class="points">
                ${p.points}
            </td>
            <td>
                ${badges}
            </td>
        </tr>

    `;
}