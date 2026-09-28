import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isLoggedIn()) return true;
  router.navigate(['/login']);
  return false;
};

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isAdmin()) return true;
  router.navigate(['/']);
  return false;
};

// Permite entrar a rol "bodega" y también a "admin" (para que pueda supervisar
// la vista de bodega sin necesitar una segunda cuenta).
export const bodegaGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isBodega() || auth.isAdmin()) return true;
  router.navigate(['/']);
  return false;
};

// Permite entrar a rol "calidad" y también a "admin" (para que pueda
// supervisar el muestreo de calidad sin necesitar una segunda cuenta).
export const calidadGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isCalidad() || auth.isAdmin()) return true;
  router.navigate(['/']);
  return false;
};