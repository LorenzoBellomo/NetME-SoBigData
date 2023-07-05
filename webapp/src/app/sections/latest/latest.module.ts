import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LatestRoutingModule } from './latest-routing.module';
import { LatestComponent } from './latest.component';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import {MatIconModule} from "@angular/material/icon";
import {MaterialModule} from "../../material.component";


@NgModule({
  declarations: [
    LatestComponent
  ],
  imports: [
    CommonModule,
    LatestRoutingModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatIconModule,
    MaterialModule,
  ]
})
export class LatestModule { }
