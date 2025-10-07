function getDisplayName(user) {
    if (user.prenom && user.nom) {
        return `${user.prenom} ${user.nom}`;
    } else if (user.prenom) {
        return user.prenom;
    } else if (user.nom) {
        return user.nom;
    } else {
        return user.email.split('@')[0];
    }
}

let currentUser = null;

async function checkAuth() {
    try {
        const response = await fetch('http://localhost:8080/auth/check', {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (!data.authenticated) {
            window.location.href = '/connexion/connexion';
            return null;
        }
        
        currentUser = data.user;
        return data.user;
        
    } catch (error) {
        console.error('Erreur vérification auth:', error);
        window.location.href = '/connexion/connexion';
        return null;
    }
}

function getGreeting() {
    const now = new Date();
    const hour = now.getHours();
    
    if (hour >= 6 && hour < 18) {
        return "Bonjour";
    } else {
        return "Bonsoir";
    }
}

// Fonction pour calculer l'âge à partir de la date de naissance
function calculateAge(birthdate) {
    const today = new Date();
    const birth = new Date(birthdate);
    
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    // Si on n'a pas encore eu l'anniversaire cette année
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}


async function updateGreeting() {
    const greetingElement = document.getElementById('dynamicGreeting');
    const greeting = getGreeting();
    
    if (!greetingElement) return;
    
    if (!currentUser) {
        const user = await checkAuth();
        if (!user) return;
    }
    
    if (currentUser) {
        const username = getDisplayName(currentUser);
        greetingElement.textContent = `${greeting} ${username}`;
    } else {
        greetingElement.textContent = greeting;
    }
}

async function updateAge() {
    const ageElement = document.getElementById('dynamicAge');
    if (!ageElement) return;

    if (!currentUser) {
        currentUser = await checkAuth();
        if (!currentUser) return;
    }

    let birthdate = currentUser.date_naissance;

    if (Array.isArray(birthdate)) {
        birthdate = birthdate[0];
    }

    if (!birthdate || birthdate.trim() === "") {
        ageElement.textContent = "";
        return;
    }

    const parsedDate = new Date(birthdate);
    if (isNaN(parsedDate.getTime())) {
        ageElement.textContent = "";
        return;
    }

    const age = calculateAge(parsedDate);
    ageElement.textContent = age > 0 ? `${age} ans` : "";
}

document.addEventListener('DOMContentLoaded', async function() {
    console.log('conversation-utils.js: Mise à jour salutations');
    await updateGreeting();
    await updateAge();
});

setInterval(updateGreeting, 60000);

window.ConversationPageUtils = {
    updateGreeting,
    updateAge
};