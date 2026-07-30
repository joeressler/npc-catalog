import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, of, shareReplay, tap } from 'rxjs';

interface AuthUser {
  username: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/auth';

  readonly username = signal<string | null>(null);
  readonly authenticated = signal(false);

  private sessionCheck$: Observable<boolean> | null = null;

  /** Resolve current session once; subsequent calls reuse the result until cleared. */
  ensureSession(): Observable<boolean> {
    if (this.authenticated()) {
      return of(true);
    }
    if (!this.sessionCheck$) {
      this.sessionCheck$ = this.http.get<AuthUser>(`${this.base}/me/`).pipe(
        map((user) => {
          this.username.set(user.username);
          this.authenticated.set(true);
          return true;
        }),
        catchError(() => {
          this.clearLocalSession();
          return of(false);
        }),
        shareReplay(1),
      );
    }
    return this.sessionCheck$;
  }

  login(username: string, password: string): Observable<AuthUser> {
    return this.http.post<AuthUser>(`${this.base}/login/`, { username, password }).pipe(
      tap((user) => {
        this.username.set(user.username);
        this.authenticated.set(true);
        this.sessionCheck$ = null;
      }),
    );
  }

  logout(): Observable<{ ok: boolean }> {
    return this.http.post<{ ok: boolean }>(`${this.base}/logout/`, {}).pipe(
      tap(() => this.clearLocalSession()),
      catchError(() => {
        this.clearLocalSession();
        return of({ ok: true });
      }),
    );
  }

  clearLocalSession(): void {
    this.username.set(null);
    this.authenticated.set(false);
    this.sessionCheck$ = null;
  }
}
