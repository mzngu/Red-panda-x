import { test, expect } from '@playwright/test';

test.describe('Page Chatbot', () => {
  test('devrait afficher l\'interface de chat', async ({ page }) => {
    await page.goto('/chatbot/chatbot');
    await page.waitForLoadState('networkidle');
    
    // Vérifier le titre
    await expect(page.locator('.greeting')).toContainText('Parles avec Sorrel');
    
    // Vérifier la présence des éléments du chat
    await expect(page.locator('#upload-button')).toBeVisible();
    await expect(page.locator('#chat-input')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Vérifier le logo
    await expect(page.locator('.header-logo')).toBeVisible();
  });

  test('devrait pouvoir uploader une image', async ({ page }) => {
    await page.goto('/chatbot/chatbot');
    await page.waitForLoadState('networkidle');
    
    // Créer un fichier de test
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('#upload-button');
    const fileChooser = await fileChooserPromise;
    
    // Simuler la sélection d'un fichier
    await fileChooser.setFiles({
      name: 'test-prescription.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('fake-image-data')
    });
    
    // Vérifier que l'aperçu est affiché
    await expect(page.locator('#image-preview')).not.toHaveClass(/hidden/);
  });

  test('devrait pouvoir envoyer un message', async ({ page }) => {
    await page.goto('/chatbot/chatbot');
    await page.waitForLoadState('networkidle');
    
    // Attendre que la connexion soit établie
    await expect(page.locator('#chat-messages')).toContainText('[Connecté au serveur]', { timeout: 10000 });
    
    // Vérifier que le champ est vide
    await expect(page.locator('#chat-input')).toHaveValue('');
    
    // Taper un message
    await page.fill('#chat-input', 'Bonjour Sorrel');
    await page.click('button[type="submit"]');
    
    // Vérifier que le message apparaît dans le chat avec un timeout plus long
    await expect(page.locator('#chat-messages')).toContainText('Bonjour Sorrel', { timeout: 30000 });
    
    // Vérifier que le champ de saisie est vidé
    await expect(page.locator('#chat-input')).toHaveValue('');
  });
});