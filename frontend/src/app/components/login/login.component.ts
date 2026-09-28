import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html'
})
export class LoginComponent {
  username = '';
  password = '';
  error = '';
  cargando = false;
  mostrarPassword = false;

  constructor(private auth: AuthService, private router: Router) {}

  login(): void {
    if (!this.username || !this.password) {
      this.error = 'Ingresa usuario y contraseña.';
      return;
    }
    this.cargando = true;
    this.error = '';
    this.auth.login(this.username, this.password).subscribe({
      next: (res) => {
        this.cargando = false;
        if (res.rol === 'admin') {
          this.router.navigate(['/admin']);
        } else if (res.rol === 'bodega') {
          this.router.navigate(['/bodega']);
        } else if (res.rol === 'calidad') {
          this.router.navigate(['/calidad']);
        } else {
          this.router.navigate(['/bobinas']);
        }
      },
      error: (err) => {
        this.cargando = false;
        this.error = err.error?.detail ?? 'Error al iniciar sesión.';
      }
    });
  }
}