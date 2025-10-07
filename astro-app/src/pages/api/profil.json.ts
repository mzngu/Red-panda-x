import type { APIRoute } from 'astro';
import { DatabaseService } from '../../../../services/database_service';

export const GET: APIRoute = async () => {
  try {
    const dbService = new DatabaseService();
    const profil = await dbService.getProfilUtilisateur(1);

    if (!profil) {
      return new Response(JSON.stringify({ message: 'Utilisateur non trouvé' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify(profil), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error(error);
    return new Response(JSON.stringify({ message: 'Erreur interne du serveur' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
