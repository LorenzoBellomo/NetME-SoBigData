import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeConfigResolver, ResultsConfigResolver } from './core/messages-config.resolver';
import { NetmeComponent } from './netme/netme.component';

const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    component: NetmeComponent,
    resolve: { t1: HomeConfigResolver }
  },
  { path: 'latest', loadChildren: () => import('./sections/latest/latest.module').then(m => m.LatestModule) },
  { path: 'how-it-works', loadChildren: () => import('./sections/how-it-works/how-it-works.module').then(m => m.HowItWorksModule) },
  {
    path: 'results',
    loadChildren: () => import('./sections/results/results.module').then(m => m.ResultsModule),
    resolve: { t1: ResultsConfigResolver }
  },
  { path: 'about-us', loadChildren: () => import('./sections/about-us/about-us.module').then(m => m.AboutUsModule) },
  {
    path: '**',
    pathMatch: 'full',
    redirectTo: ''
  }

];


@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
