import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { ApiService } from './api.service';
import { EncounterWritePayload, SessionWritePayload } from '../models/domain.models';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('createSession POSTs a JSON body including npc_ids', () => {
    const payload: SessionWritePayload = {
      title: 'Heist at the Docks',
      npc_ids: [1, 2, 3],
      encounter_ids: [9],
    };

    service.createSession(7, payload).subscribe();

    const req = httpMock.expectOne('/api/campaigns/7/sessions/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.npc_ids).toEqual([1, 2, 3]);
    expect(req.request.body.encounter_ids).toEqual([9]);
    req.flush({});
  });

  it('createEncounter POSTs a JSON body including npc_ids', () => {
    const payload: EncounterWritePayload = {
      title: 'Ambush at Weathertop',
      npc_ids: [4, 5],
    };

    service.createEncounter(7, payload).subscribe();

    const req = httpMock.expectOne('/api/campaigns/7/encounters/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.npc_ids).toEqual([4, 5]);
    expect(req.request.body.title).toBe('Ambush at Weathertop');
    req.flush({});
  });
});
