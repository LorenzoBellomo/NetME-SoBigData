import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NetmeComponent } from './netme.component';

describe('NetmeComponent', () => {
  let component: NetmeComponent;
  let fixture: ComponentFixture<NetmeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NetmeComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NetmeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
