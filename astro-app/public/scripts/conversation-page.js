const ConversationUtils = (() => {
  const LS_KEY = "dp_conversations";

  function loadConversations() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  }
  function saveConversations(list) {
    try { localStorage.setItem(LS_KEY, JSON.stringify(list || [])); } catch {}
  }
  function formatRelativeDate(dateString) {
    const date = new Date(dateString);
    const now  = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000*60*60*24));

    if (diffDays === 0) return "Aujourd'hui";
    if (diffDays === 1) return "Hier";
    if (diffDays < 7)   return `Il y a ${diffDays} jours`;
    if (diffDays < 30) {
      const weeks = Math.floor(diffDays/7);
      return `Il y a ${weeks} semaine${weeks>1?'s':''}`;
    }
    return date.toLocaleDateString('fr-FR');
  }

  function ensureDefaults() {
    let conversations = loadConversations();
    if (conversations.length === 0) {
      conversations = [
        {
          id: Date.now()-30000,
          titre: "Titre 1",
          date_derniere_activite: new Date(Date.now()-24*60*60*1000).toISOString(),
          nb_messages: 2,
          _local: true
        },
        {
          id: Date.now()-20000,
          titre: "Titre 2",
          date_derniere_activite: new Date(Date.now()-3*24*60*60*1000).toISOString(),
          nb_messages: 5,
          _local: true
        },
        {
          id: Date.now()-10000,
          titre: "Titre 3",
          date_derniere_activite: new Date(Date.now()-10*24*60*60*1000).toISOString(),
          nb_messages: 1,
          _local: true
        }
      ];
      saveConversations(conversations);
    }
    return conversations;
  }

  return { loadConversations, saveConversations, formatRelativeDate, ensureDefaults };
})();

document.addEventListener('DOMContentLoaded', async function () {
  await loadAndDisplayConversations();

  if (window.PrescriptionPageUtils?.refreshPrescriptionsDisplay) {
    window.PrescriptionPageUtils.refreshPrescriptionsDisplay();
  }

  initializeSearch();

  setInterval(updateRelativeDates, 60000);
});

async function loadAndDisplayConversations() {
  const conversationsSection = document.querySelector('.conversations-section');

  let conversations = null;
  try {
    const res = await fetch('http://localhost:8080/conversations/', {
      credentials: 'include'
    });
    if (res.ok) {
      conversations = await res.json();
      ConversationUtils.saveConversations(conversations);
    }
  } catch (e) {
    console.warn("[conversations] API indisponible, fallback local :", e?.message || e);
  }

  if (!Array.isArray(conversations)) {
    conversations = ConversationUtils.loadConversations();
    if (!conversations || conversations.length === 0) {
      conversations = ConversationUtils.ensureDefaults();
    }
  }

  displayConversations(conversationsSection, conversations);
}

function displayConversations(conversationsSection, conversations) {
  if (!conversationsSection) return;

  const existingItems = conversationsSection.querySelectorAll('.conversation-item, .no-conversations');
  existingItems.forEach(el => el.remove());

  if (!conversations || conversations.length === 0) {
    displayNoConversations(conversationsSection);
    return;
  }

  // Tri du + récent au + ancien
  const sorted = [...conversations].sort((a,b) =>
    new Date(b.date_derniere_activite) - new Date(a.date_derniere_activite)
  );

  sorted.forEach(conv => {
    const el = createConversationElement(conv);
    conversationsSection.appendChild(el);
  });
}

function getTrashSVG() {
  return `
  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M9 3h6M5 7h14M18 7l-.7 12a2 2 0 0 1-2 1.9H8.7a2 2 0 0 1-2-1.9L6 7m4 3v7m4-7v7"
          stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`;
}

function createConversationElement(conversation) {
  const div = document.createElement('div');
  div.className = 'conversation-item';
  div.dataset.id   = conversation.id;
  div.dataset.date = conversation.date_derniere_activite;

  const formattedDate = ConversationUtils.formatRelativeDate(conversation.date_derniere_activite);

  div.innerHTML = `
    <div class="conversation-content">
      <div class="conversation-title">${escapeHtml(conversation.titre || 'Conversation')}</div>
      <div class="conversation-meta">
        <span class="conversation-date">${formattedDate}</span>
      </div>
    </div>
  `;

  const actionsDiv = document.createElement('div');
  actionsDiv.className = 'conversation-actions';

  const msgCount = document.createElement('span');
  msgCount.className = 'message-count';
  msgCount.textContent = `${conversation.nb_messages || 0} messages`;

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'action-btn delete-btn bin-icon';
  deleteBtn.type = 'button';
  deleteBtn.setAttribute('aria-label', 'Supprimer la conversation');
  deleteBtn.setAttribute('title', 'Supprimer');
  deleteBtn.innerHTML = getTrashSVG(); 
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
    deleteConversation(conversation.id, !!conversation._local);
  };


  actionsDiv.appendChild(msgCount);

  actionsDiv.appendChild(deleteBtn);
  div.appendChild(actionsDiv);

  // Ouvre la conversation
  div.addEventListener('click', () => openConversation(conversation.id));

  return div;
}


function displayNoConversations(conversationsSection) {
  const existing = conversationsSection.querySelectorAll('.conversation-item, .no-conversations');
  existing.forEach(i => i.remove());

  const noDiv = document.createElement('div');
  noDiv.className = 'no-conversations';
  noDiv.innerHTML = `
    <div style="text-align: center; padding: 40px; color: #6b7280;">
      <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
      <p style="font-size: 18px; margin-bottom: 8px;">Aucune conversation</p>
      <p style="font-size: 14px;">Commence une nouvelle conversation avec Sorrel !</p>
      <button onclick="startNewConversation()" style="
          margin-top: 16px;
          background: linear-gradient(135deg, #f97316, #ea580c);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 20px;
          font-weight: 500;
          cursor: pointer;">
        Nouvelle conversation
      </button>
    </div>
  `;
  conversationsSection.appendChild(noDiv);
}

function initializeSearch() {
  const searchInput = document.getElementById('conversationSearch');
  const clearButton = document.getElementById('clearSearch');
  if (!searchInput || !clearButton) return;

  searchInput.addEventListener('input', function () {
    const term = this.value.toLowerCase().trim();
    clearButton.style.display = term.length > 0 ? 'flex' : 'none';
    filterConversations(term);

    if (window.PrescriptionPageUtils?.filterPrescriptions) {
      window.PrescriptionPageUtils.filterPrescriptions(term);
    }
  });

  clearButton.addEventListener('click', function () {
    searchInput.value = '';
    clearButton.style.display = 'none';
    filterConversations('');

    if (window.PrescriptionPageUtils?.filterPrescriptions) {
      window.PrescriptionPageUtils.filterPrescriptions('');
    }
    searchInput.focus();
  });
}

function filterConversations(term) {
  const items = document.querySelectorAll('.conversation-item');
  items.forEach(item => {
    const title = item.querySelector('.conversation-title')?.textContent.toLowerCase() || '';
    const date  = item.querySelector('.conversation-date')?.textContent.toLowerCase() || '';
    const show  = term === '' || title.includes(term) || date.includes(term);
    item.style.display = show ? 'flex' : 'none';
    item.style.opacity = show ? '1' : '0';
  });
}

function openConversation(conversationId) {
  window.location.href = `/chatbot/chatbot?conversation_id=${encodeURIComponent(conversationId)}`;
}

async function deleteConversation(id, isLocal = false) {
  if (!confirm("Êtes-vous sûr de vouloir supprimer cette conversation ?")) return;

  if (!isLocal) {
    try {
      const res = await fetch(`http://localhost:8080/conversations/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        await loadAndDisplayConversations();
        return;
      }
      console.warn("[conversations] Suppression API échouée, fallback local");
    } catch (e) {
      console.warn("[conversations] Erreur réseau suppression API, fallback local");
    }
  }

  const list = ConversationUtils.loadConversations();
  ConversationUtils.saveConversations(list.filter(c => String(c.id) !== String(id)));
  await loadAndDisplayConversations();
}

function startNewConversation() {
  window.location.href = '/chatbot/chatbot';
}

function updateRelativeDates() {
  const items = document.querySelectorAll('.conversation-item');
  items.forEach(item => {
    const el  = item.querySelector('.conversation-date');
    const iso = item.dataset.date;
    if (iso && el) el.textContent = ConversationUtils.formatRelativeDate(iso);
  });
}

window.ConversationPageUtils = {
  openConversation,
  deleteConversation,
  startNewConversation,
  loadAndDisplayConversations,
  updateRelativeDates
};

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, s => (
    { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[s]
  ));
}
