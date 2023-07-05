import { Component, Inject, OnInit } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-highlight-dialog',
  templateUrl: './highlight-dialog.component.html',
  styleUrls: ['./highlight-dialog.component.css']
})
export class HighlightDialogComponent implements OnInit {

  innerHTML = ''
  label = ''

  constructor(public dialogRef: MatDialogRef<HighlightDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any) {
    this.innerHTML = data.innerHTML
    this.label = data.label
  }

  ngOnInit(): void {
  }

  onOkClick() {
    this.dialogRef.close()
  }

}
