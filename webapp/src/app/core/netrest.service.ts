import { RequestData } from './models/request-data.model';
import { retry, catchError } from 'rxjs/operators';
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from "@angular/common/http";
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from 'src/environments/environment';

@Injectable({
    providedIn: 'root'
})
export class NetRESTService {

    private httpOptions = {
        headers: new HttpHeaders({
            'Content-Type': 'application/json'
        })
    }

    constructor(private httpClient: HttpClient) { }

    handleError(err: HttpErrorResponse): Observable<any> {
        if (err.error instanceof Error) // client-side or network
            console.error('An error occurred:', err.error.message)
        else // backend returned an unsuccessful response
            console.error(`Backend returned code ${err.status}, body was: ${err.error}`);

        return new BehaviorSubject({ status: 500 })
    }

    // TODO: sanitize etc
    startSearch(searchData: RequestData): Observable<any> {
        console.log(searchData)
        return this.httpClient.post<any>(environment.apiURL + "/send_data", { ...searchData }, this.httpOptions)
            .pipe(
                retry(2),
                catchError(this.handleError)
            )
    }

    querySearch(id: string): Observable<any> {
        return this.httpClient.get<any>(environment.apiURL + "/items/" + id, this.httpOptions)
            .pipe(
                retry(2),
                catchError(this.handleError)
            )
    }

    networkDelete(id: string): Observable<any>{
        return this.httpClient.get<any>(environment.apiURL + "/delete/" + id, this.httpOptions)
            .pipe(retry(2), catchError(this.handleError))
    }
}
