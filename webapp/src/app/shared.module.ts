import { NgModule } from '@angular/core';

import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { SearchTableComponent } from './shared/search-table/search-table.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { CommonModule } from '@angular/common';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RouterModule } from '@angular/router';
import { MaterialModule } from './material.component';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HighlightDialogComponent } from './shared/highlight-dialog/highlight-dialog.component';
import { CategoryPickerComponent } from './shared/category-picker/category-picker.component';
import { PopupComponent } from './shared/popup/popup.component';
import { ErrorPageComponent } from './shared/error-page/error-page.component';
import { SafeHtmlPipe } from './shared/pipes/safe-html.pipe';
import { FileUploadComponent } from './shared/file-upload/file-upload.component';
import { MessageInfoComponent } from './shared/message-info/message-info.component';
import { SelectFromApiComponent } from './shared/selectfromapi/select-from-api.component';
import { MatSelectModule } from '@angular/material/select';
import { NgxMatSelectSearchModule } from 'ngx-mat-select-search';

@NgModule({
  declarations: [
    SearchTableComponent,
    HighlightDialogComponent,
    CategoryPickerComponent,
    PopupComponent,
    ErrorPageComponent,
    FileUploadComponent,
    SafeHtmlPipe,
    MessageInfoComponent,
    SelectFromApiComponent
  ],
  imports: [
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatIconModule,
    MatTooltipModule,
    MatListModule,
    MatGridListModule,
    MaterialModule,
    MatProgressSpinnerModule,
    RouterModule,
    CommonModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    NgxMatSelectSearchModule,
    ReactiveFormsModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [],
  exports: [
    SearchTableComponent,
    CategoryPickerComponent,
    PopupComponent,
    ErrorPageComponent,
    FileUploadComponent,
    MessageInfoComponent,
    SelectFromApiComponent
  ]
})
export class SharedModule { }
