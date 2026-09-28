import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  template: `
    <div *ngIf="auth.isLoggedIn() && !auth.isAdmin(); else fullPage" class="min-h-screen bg-gray-100">
      <!-- NAVEGACIÓN operario -->
      <nav class="no-print bg-white shadow-sm border-b border-gray-200 px-4 py-3">
        <div class="max-w-6xl mx-auto flex flex-wrap gap-2 justify-between items-center">
          <div class="flex flex-wrap gap-2">
            <a routerLink="/bobinas" routerLinkActive="!bg-brand-blue !text-white !border-brand-blue"
               class="px-4 py-2.5 min-h-[44px] flex items-center gap-1.5 bg-white text-gray-600 border-2 border-gray-200 font-bold rounded-full text-xs transition-colors">
              <span class="material-symbols-outlined text-[18px]">inventory_2</span> Bobinas
            </a>
            <a routerLink="/rotulado" routerLinkActive="!bg-brand-blue !text-white !border-brand-blue"
               class="px-4 py-2.5 min-h-[44px] flex items-center gap-1.5 bg-white text-gray-600 border-2 border-gray-200 font-bold rounded-full text-xs transition-colors">
              <span class="material-symbols-outlined text-[18px]">sell</span> Rotulado
            </a>
            <a routerLink="/pesos" routerLinkActive="!bg-brand-blue !text-white !border-brand-blue"
               class="px-4 py-2.5 min-h-[44px] flex items-center gap-1.5 bg-white text-gray-600 border-2 border-gray-200 font-bold rounded-full text-xs transition-colors">
              <span class="material-symbols-outlined text-[18px]">monitor_weight</span> Pesos
            </a>
            <a routerLink="/pesos-enfardadora" routerLinkActive="!bg-brand-blue !text-white !border-brand-blue"
               class="px-4 py-2.5 min-h-[44px] flex items-center gap-1.5 bg-white text-gray-600 border-2 border-gray-200 font-bold rounded-full text-xs transition-colors">
              <span class="material-symbols-outlined text-[18px]">package_2</span> Peso Enfardadoras
            </a>
            <a routerLink="/mermas" routerLinkActive="!bg-brand-blue !text-white !border-brand-blue"
               class="px-4 py-2.5 min-h-[44px] flex items-center gap-1.5 bg-white text-gray-600 border-2 border-gray-200 font-bold rounded-full text-xs transition-colors">
              <span class="material-symbols-outlined text-[18px]">trending_down</span> Mermas
            </a>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <div class="text-xs font-bold text-gray-700">{{ auth.getNombre() }}</div>
              <div class="text-[10px] font-mono text-gray-400">{{ auth.getMaquinas() || 'Sin máquina asignada' }}</div>
            </div>
            <button (click)="logout()"
              class="px-4 py-2.5 min-h-[44px] bg-white text-brand-red border-2 border-brand-red/30 text-xs font-bold rounded-full hover:bg-red-50 transition-colors">
              Salir
            </button>
          </div>
        </div>
      </nav>
      <div class="p-4">
        <router-outlet />
      </div>
    </div>

    <ng-template #fullPage>
      <router-outlet />
    </ng-template>
  `
})
export class AppComponent {
  constructor(public auth: AuthService, private router: Router) {}

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
