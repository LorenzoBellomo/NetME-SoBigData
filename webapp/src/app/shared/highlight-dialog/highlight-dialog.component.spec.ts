import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HighlightDialogComponent } from './highlight-dialog.component';

describe('HighlightDialogComponent', () => {
  let component: HighlightDialogComponent;
  let fixture: ComponentFixture<HighlightDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ HighlightDialogComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HighlightDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
