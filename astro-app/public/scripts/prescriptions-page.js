(function () {
  let prescriptionsCache = [];
  let currentSort = 'desc'; // 'asc' | 'desc'

  // Nouvelle fonction pour charger les données depuis l'API
  async function fetchPrescriptions() {
    try {
      const response = await fetch('/api/ordonnances'); // L'URL de votre nouvelle API
      if (!response.ok) {
        console.error("Erreur lors de la récupération des ordonnances:", response.statusText);
        if (response.status === 401) {
          // Rediriger vers la page de connexion si l'utilisateur n'est pas authentifié
          window.location.href = '/auth/login';
        }
        return [];
      }
      const data = await response.json();
      prescriptionsCache = data; 
      return data;
    } catch (error) {
      console.error("Erreur réseau ou JSON:", error);
      return [];
    }
  }

  const fmt = (iso) => {
    try {
      return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' });
    } catch { return iso; }
  };

  function sortItems(items, dir = currentSort) {
    return [...items].sort((a, b) => {
      const da = new Date(a.date).getTime();
      const db = new Date(b.date).getTime();
      return dir === 'asc' ? da - db : db - da;
    });
  }

  async function render() {
    const grid = document.getElementById('prescriptionsGrid');
    if (!grid) return;

    // Affiche un indicateur de chargement
    grid.innerHTML = '<p style="color:#6b7280">Chargement des ordonnances...</p>';

    const items = await fetchPrescriptions();
    const sortedItems = sortItems(items);

    if (!sortedItems.length) {
      grid.innerHTML = '<p style="color:#6b7280">Aucune ordonnance pour le moment.</p>';
      return;
    }

    grid.innerHTML = sortedItems.map(p => {
      const title = p.title || 'Ordonnance';
      const sub = p.doctor ? p.doctor : fmt(p.date);
      return `
        <div class="prescription-cell"
             data-id="${p.id}"
             data-title="${(title).toLowerCase()}"
             data-doctor="${(p.doctor||'').toLowerCase()}"
             data-tags="${(p.tags||[]).join(' ').toLowerCase()}">
          <article class="prescription-tile">
            <img src="${p.image || '/images/dna.png'}" alt="${title}" />
          </article>
          <div class="prescription-caption" title="${title}">
            ${title}
            <span class="prescription-sub" title="${sub}">${sub || ''}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  function filterPrescriptions(q) {
    const cards = document.querySelectorAll('#prescriptionsGrid .prescription-cell');
    const query = (q || '').toLowerCase().trim();
    cards.forEach(card => {
      const hay = `${card.dataset.title||''} ${card.dataset.doctor||''} ${card.dataset.tags||''}`;
      const show = !query || hay.includes(query);
      card.style.display = show ? '' : 'none';
      card.style.opacity = show ? '1' : '0';
    });
  }

  // Ces fonctions ne sont plus nécessaires car les données sont gérées côté serveur.
  // Vous pouvez les remplacer par des appels API si vous implémentez la création/suppression côté client.
  function createNewPrescription({ title, doctor, tags = [], image = '/images/dna.png' }) {
    console.warn("La création de nouvelles ordonnances doit être implémentée via l'API.");
  }

  function deletePrescriptionById(id) {
    console.warn("La suppression d'ordonnances doit être implémentée via l'API.");
  }

  function sortPrescriptions(dir) {
    currentSort = dir === 'asc' ? 'asc' : 'desc';
    // Re-render avec le cache pour éviter un appel réseau
    const sortedItems = sortItems(prescriptionsCache);
    render(sortedItems); // On passe les données triées pour éviter un nouveau fetch
  }

  document.addEventListener('DOMContentLoaded', () => {
    // On n'a plus besoin de ensureDefaults, on appelle directement render.
    render();
  });

  // API globale
  window.PrescriptionPageUtils = {
    refreshPrescriptionsDisplay: render,
    filterPrescriptions,
    createNewPrescription,
    deletePrescriptionById,
    sortPrescriptions
  };
})();
