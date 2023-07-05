import { Injectable } from "@angular/core";
import { AngularFireDatabase } from '@angular/fire/compat/database';
import { ConfigMessage } from "./models/config-message.model";


@Injectable({
    providedIn: 'root'
})
export class DatabaseService {

    constructor(private db: AngularFireDatabase) {
    }

    async loadConfig(kind: 'home' | 'results'): Promise<ConfigMessage[]> {
        const ds = await this.db.object(`/appConfig/${kind}/messages`).query.once("value")
        if (ds.exists()) return ds.val() as ConfigMessage[]
        return []
    }
}
