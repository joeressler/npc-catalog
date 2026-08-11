import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, of, shareReplay, tap } from 'rxjs';

export type AuthRole = 'dm' | 'player';

interface AuthUser {
  username: string;
  role: AuthRole;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/auth';

  readonly username = signal<string | null>(null);
  readonly role = signal<AuthRole | null>(null);
  readonly authenticated = signal(false);
  readonly isDm = computed(() => this.role() === 'dm');
  readonly isPlayer = computed(() => this.role() === 'player');
  readonly isReadonly = computed(() => this.role() === 'player');

  private sessionCheck$: Observable<boolean> | null = null;

  /** Resolve current session once; subsequent calls reuse the result until cleared. */
  ensureSession(): Observable<boolean> {
    if (this.authenticated()) {
      return of(true);
    }
    if (!this.sessionCheck$) {
      this.sessionCheck$ = this.http.get<AuthUser>(`${this.base}/me/`).pipe(
        map((user) => {
          this.applyUser(user);
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
        this.applyUser(user);
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
    this.role.set(null);
    this.authenticated.set(false);
    this.sessionCheck$ = null;
  }

  private applyUser(user: AuthUser): void {
    this.username.set(user.username);
    this.role.set(user.role === 'player' ? 'player' : 'dm');
    this.authenticated.set(true);
  }
}
