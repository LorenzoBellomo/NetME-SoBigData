import { Injectable } from '@angular/core';
import { StorageMap } from '@ngx-pwa/local-storage';
import { nanoid } from 'nanoid';
import moment from 'moment';
import { Search } from './models/search.model';
import {Router} from "@angular/router";
import {NetRESTService} from "./netrest.service";
import {element} from "protractor";
import {MatTableDataSource} from "@angular/material/table";


@Injectable({
    providedIn: 'root'
})
export class SessionService {

    constructor(private storage: StorageMap, private netRestService: NetRESTService) {
        //this.checkToken()
    }

    checkToken() {
        this.storage.get('token').subscribe((v: any) => {
            console.log("token is", v)
            if (!v || !v.expiration || moment().isAfter(moment(v.expiration))) {
                const newToken = nanoid(24)
                console.log("new token is", newToken)
                this.storage.set('token', { key: newToken, expiration: moment().add(90, 'days').format("YYYY-MM-DDTHH:mm:ss") }).subscribe(() => { })
            }
        })
    }

    saveSearch(search: Search) {
        this.storage.get('latest').subscribe((v: any) => {
            let latest: Search[] = (v || []) as Search[]
            latest.push(search)
            this.storage.set('latest', latest).subscribe(() => { })
        })
    }

    loadLatestSearch(): Promise<Search[] | undefined> {
        return this.storage.get('latest').toPromise() as Promise<Search[] | undefined>
    }

    deleteItem(itemId:string) {
        const resp = this.netRestService.networkDelete(itemId)
        console.log(resp.subscribe(() => {}))
    }

    updateItems(latest: Search[]){
        this.storage.set('latest', latest).subscribe(() => { })
    }
}
