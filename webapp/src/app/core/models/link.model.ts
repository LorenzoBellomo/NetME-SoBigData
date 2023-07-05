import { ArticleType } from "./enums";

export interface Article {
    type: ArticleType;
    key: string;
    link: string;
    name: string;
}