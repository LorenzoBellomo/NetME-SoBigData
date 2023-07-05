import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ResultsRoutingModule } from './results-routing.module';
import { ResultsComponent } from './results.component';
import { MatSliderModule } from '@angular/material/slider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatRadioModule } from '@angular/material/radio';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from '../../shared.module';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule } from '@angular/material/sort';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatButtonModule } from '@angular/material/button';
import { ConsoleComponent } from './console/console.component';
import { MatCardModule } from '@angular/material/card';
import { FlexLayoutModule } from '@angular/flex-layout';
import { MaterialModule } from '../../material.component';
import { MatStepperModule } from '@angular/material/stepper';
import { LayoutModule } from '@angular/cdk/layout';
import { RouterModule } from '@angular/router';



@NgModule({
  declarations: [
    ResultsComponent,
    ConsoleComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ResultsRoutingModule,
    MatSliderModule,
    MatInputModule,
    MatIconModule,
    MatTooltipModule,
    MatExpansionModule,
    MatSliderModule,
    MatRadioModule,
    SharedModule,
    MatProgressSpinnerModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatButtonModule,
    MatCardModule,
    FlexLayoutModule,
    MaterialModule,
    MatStepperModule,
    RouterModule,
    ReactiveFormsModule,
    LayoutModule,
  ]
})
export class ResultsModule { }
