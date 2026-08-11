import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs';

import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return auth.ensureSession().pipe(
    map((ok) => {
      if (ok) {
        return true;
      }
      return router.createUrlTree(['/login'], {
        queryParams: { returnUrl: state.url || '/' },
      });
    }),
  );
};

/** Send already-authenticated users away from the login screen. */
export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return auth.ensureSession().pipe(
    map((ok) => (ok ? router.createUrlTree(['/']) : true)),
  );
};

/** DM-only routes: create/edit forms and sessions/encounters. */
export const dmGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return auth.ensureSession().pipe(
    map((ok) => {
      if (!ok) {
        return router.createUrlTree(['/login'], {
          queryParams: { returnUrl: state.url || '/' },
        });
      }
      if (auth.isDm()) {
        return true;
      }
      const match = state.url.match(/\/campaigns\/(\d+)/);
      if (match) {
        return router.createUrlTree(['/campaigns', match[1]]);
      }
      return router.createUrlTree(['/']);
    }),
  );
};
