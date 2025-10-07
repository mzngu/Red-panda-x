import { test, expect } from '@playwright/test';

test.describe('Page Prescription', () => {
  test('devrait afficher l\'interface de scan d\'ordonnance', async ({ page }) => {
    await page.goto('/prescription/prescription');
    await page.waitForLoadState('networkidle');
    
    // Vérifier le titre
    await expect(page.locator('.greeting')).toContainText('Scan ton ordonnance');
    
    // Vérifier la présence du bouton d'upload
    await expect(page.locator('#upload-button')).toBeVisible();
    await expect(page.locator('#upload-button')).toContainText('Prendre une photo de l\'ordonnance');
    
    // Vérifier le logo spécifique
    await expect(page.locator('img[src="/sorrel/pandaPrescription.png"]')).toBeVisible();
  });

  test('devrait pouvoir uploader une ordonnance', async ({ page }) => {
    await page.goto('/prescription/prescription');
    await page.waitForLoadState('networkidle');
    
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('#upload-button');
    const fileChooser = await fileChooserPromise;
    
    await fileChooser.setFiles({
      name: 'ordonnance.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('fake-prescription-image')
    });
    
    // Vérifier que l'image est prévisualisée
    await expect(page.locator('#image-preview')).not.toHaveClass(/hidden/);
  });
});