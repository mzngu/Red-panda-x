import { test, expect } from '@playwright/test';

test.describe('Page d\'accueil', () => {
  test('devrait afficher le titre et les boutons d\'authentification', async ({ page }) => {
    await page.goto('/');
    
    // Vérifier le titre
    await expect(page).toHaveTitle("Don't Panic - Accueil");
    await expect(page.locator('h1')).toContainText("DON'T PANIC");
    
    // Vérifier la présence des boutons
    await expect(page.locator('text=S\'INSCRIRE')).toBeVisible();
    await expect(page.locator('text=SE CONNECTER')).toBeVisible();
    
    // Vérifier le lien vers le site de démonstration
    await expect(page.locator('text=Accéder aux site (démo)')).toBeVisible();
  });

  test('devrait naviguer vers la page d\'inscription', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=S\'INSCRIRE');
    await expect(page).toHaveURL('/inscription/inscription');
    await expect(page.locator('text=Inscription')).toBeVisible();
  });

  test('devrait naviguer vers la page de connexion', async ({ page }) => {
    await page.goto('/');
    
    await page.click('text=SE CONNECTER');
    await expect(page).toHaveURL('/connexion/connexion');
    await expect(page.locator('text=Connexion')).toBeVisible();
  });
});