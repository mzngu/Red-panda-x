async function checkAuth() {
  try {
    const response = await fetch("http://localhost:8080/auth/check", { credentials: "include" });
    const data = await response.json();

    if (!data.authenticated) {
      window.location.href = "/connexion/connexion";
      return;
    }

    const user = data.user || {};
    // Utilise le booléen calculé par le back
    const isProfileComplete = !!user.isProfileComplete;

    if (!isProfileComplete && !isBypassedPath()) {
      showProfileModalAndRedirect();
      return;
    }

    // UI si profil ok
    const userControls = document.getElementById("userControls");
    const userName = document.getElementById("userName");
    if (userControls && userName) {
      userName.textContent = `Salut ${getDisplayName(user)} !`;
      userControls.style.display = "block";
    }
  } catch (error) {
    console.error("Erreur vérification auth:", error);
    window.location.href = "/connexion/connexion";
  }
}

// Fonction utilitaire : évite boucle infinie
function isBypassedPath() {
  const p = window.location.pathname;
  return (
    p.startsWith("/profile") ||   
    p.startsWith("/connexion") ||
    p.startsWith("/popupProfile")
  );
}


// Fonction de déconnexion
async function logout() {
    try {
        const response = await fetch('http://localhost:8080/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/connexion/connexion';
        }
    } catch (error) {
        console.error('Erreur déconnexion:', error);
    }
}

function showProfileModalAndRedirect() {


  const backdrop = document.createElement("div");
  backdrop.className = "dp-backdrop";
  backdrop.innerHTML = `
    <div class="dp-modal" role="dialog" aria-labelledby="dp-title" aria-modal="true">
      <h2 id="dp-title">Profil incomplet</h2>
      <p>Pour profiter de l’application, complète d’abord ton profil. Tu vas y être redirigé(e) automatiquement.</p>
      <div class="dp-actions">
        <button class="dp-btn dp-btn-primary" id="dp-go-now">Compléter mon profil</button>
        <button class="dp-btn dp-btn-ghost" id="dp-cancel">Plus tard</button>
      </div>
      <div class="dp-countdown" id="dp-countdown">Redirection dans 5 s…</div>
    </div>
  `;
  document.body.appendChild(backdrop);

  const go = () => { window.location.href = "/profile/profile"; };
  document.getElementById("dp-go-now").addEventListener("click", go);
  document.getElementById("dp-cancel").addEventListener("click", () => {
  document.body.removeChild(backdrop);
  });

  // Compte à rebours auto
  let t = 5;
  const ctn = document.getElementById("dp-countdown");
  const timer = setInterval(() => {
    t -= 1;
    if (t <= 0) {
      clearInterval(timer);
      go();
    } else {
      ctn.textContent = `Redirection dans ${t} s…`;
    }
  }, 1000);
}


// Vérifier l'auth au chargement de la page
document.addEventListener('DOMContentLoaded', checkAuth);

// Ajouter l'event listener pour la déconnexion
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

