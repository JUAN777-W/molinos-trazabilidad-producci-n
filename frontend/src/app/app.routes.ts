import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { BobinasComponent } from './components/bobinas/bobinas.component';
import { RotuladoComponent } from './components/rotulado/rotulado.component';
import { PesosComponent } from './components/pesos/pesos.component';
import { PesosEnfardadoraComponent } from './components/pesos-enfardadora/pesos-enfardadora.component';
import { AdminComponent } from './components/admin/admin.component';
import { BodegaComponent } from './components/bodega/bodega.component';
import { CalidadComponent } from './components/calidad/calidad.component';
import { EstibaRegistroComponent } from './components/estiba-registro/estiba-registro.component';
import { MermasComponent } from './components/mermas/mermas.component';
import { OeeComponent } from './components/oee/oee.component';
import { TrazabilidadComponent } from './components/trazabilidad/trazabilidad.component';
import { authGuard, adminGuard, bodegaGuard, calidadGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'bobinas',  component: BobinasComponent,  canActivate: [authGuard] },
  { path: 'rotulado', component: RotuladoComponent, canActivate: [authGuard] },
  { path: 'pesos',    component: PesosComponent,    canActivate: [authGuard] },
  { path: 'pesos-enfardadora', component: PesosEnfardadoraComponent, canActivate: [authGuard] },
  { path: 'mermas', component: MermasComponent, canActivate: [authGuard] },
  { path: 'oee', component: OeeComponent, canActivate: [authGuard] },
  { path: 'trazabilidad', component: TrazabilidadComponent, canActivate: [authGuard] },
  { path: 'admin',    component: AdminComponent,    canActivate: [authGuard, adminGuard] },
  { path: 'bodega',   component: BodegaComponent,   canActivate: [authGuard, bodegaGuard] },
  { path: 'calidad',  component: CalidadComponent,  canActivate: [authGuard, calidadGuard] },
  // Público — sin login, para el operario de montacargas de la cooperativa
  // que escanea el QR fijo de cada máquina desde su celular.
  { path: 'estiba', component: EstibaRegistroComponent },
];