import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';

/** Attach cookies on every API call; bounce to login on 401. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const withCreds = req.clone({ withCredentials: true });

  return next(withCreds).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && err.status === 401) {
        const isLogin = req.url.includes('/api/auth/login');
        const isMe = req.url.includes('/api/auth/me');
        if (!isLogin && !isMe) {
          auth.clearLocalSession();
          const returnUrl = router.url.startsWith('/login') ? '/' : router.url;
          void router.navigate(['/login'], { queryParams: { returnUrl } });
        }
      }
      return throwError(() => err);
    }),
  );
};
