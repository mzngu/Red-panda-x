import { test, expect } from '@playwright/test';

test.describe('Page des conversations', () => {
  test('devrait afficher les conversations par défaut', async ({ page }) => {
    await page.goto('/conversation/conversation');
    
    // Attendre que la page soit chargée et que le JavaScript soit exécuté
    await page.waitForLoadState('networkidle');
    
    // Vérifier le titre avec l'ID correct
    await expect(page.locator('#dynamicGreeting')).toBeVisible();
    
    // Vérifier la présence du bouton "Nouvelle"
    await expect(page.locator('#addConversationBtn')).toBeVisible();
    
    // Vérifier la barre de recherche
    await expect(page.locator('#conversationSearch')).toBeVisible();
    
    // Vérifier qu'il y a des conversations par défaut (après initialisation JS)
    await expect(page.locator('.conversation-item')).toHaveCount(3);
  });

  test('devrait pouvoir rechercher des conversations', async ({ page }) => {
    await page.goto('/conversation/conversation');
    await page.waitForLoadState('networkidle');
    
    // Attendre que les conversations soient chargées
    await page.waitForSelector('.conversation-item', { timeout: 5000 });
    
    // Rechercher "Titre 1"
    await page.fill('#conversationSearch', 'Titre 1');
    
    // Vérifier qu'une seule conversation est visible
    await expect(page.locator('.conversation-item:visible')).toHaveCount(1);
    await expect(page.locator('.conversation-title').first()).toContainText('Titre 1');
    
    // Effacer la recherche
    await page.click('#clearSearch');
    await expect(page.locator('.conversation-item:visible')).toHaveCount(3);
  });

  test('devrait pouvoir créer une nouvelle conversation', async ({ page }) => {
    await page.goto('/conversation/conversation');
    await page.waitForLoadState('networkidle');
    
    // Attendre que les conversations soient chargées
    await page.waitForSelector('.conversation-item', { timeout: 5000 });
    
    // Cliquer sur le bouton "Nouvelle"
    page.on('dialog', dialog => dialog.accept('Ma nouvelle conversation'));
    await page.click('#addConversationBtn');
    
    // Vérifier qu'une nouvelle conversation a été ajoutée
    await expect(page.locator('.conversation-item')).toHaveCount(4);
    await expect(page.locator('.conversation-title').first()).toContainText('Ma nouvelle conversation');
  });
});