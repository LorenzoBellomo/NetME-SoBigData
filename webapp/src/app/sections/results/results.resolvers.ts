import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, Resolve, Router, RouterStateSnapshot } from '@angular/router';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ResultsService } from './results.service';

@Injectable({
    providedIn: 'root'
})

@Injectable({
    providedIn: 'root'
})
export class ResultResolver implements Resolve<any> {

    constructor(
        private resultsService: ResultsService,
        private _router: Router
    ) { }

    resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any> {
        return this.resultsService.queryResult(route.paramMap.get('id') || "").pipe(
            catchError((error) => {
                this.resultsService.resultObserver.next("ERROR")
                const parentUrl = state.url.split('/').slice(0, -2).join('/');
                this._router.navigateByUrl(parentUrl);
                return throwError(error);
            })
        );
    }
}