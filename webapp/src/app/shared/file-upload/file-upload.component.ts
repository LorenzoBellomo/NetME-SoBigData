import { Component, Input, ViewChild, ElementRef, Output, EventEmitter } from "@angular/core";
import { DomSanitizer } from '@angular/platform-browser';

@Component({
	selector: 'file-upload',
	templateUrl: './file-upload.component.html',
	styleUrls: ['./file-upload.component.css']
})
export class FileUploadComponent {
	@Input() mode: any
	@Input() names: any
	@Input() url: any
	@Input() method: any
	@Input() multiple: boolean = false
	@Input() disabled: any
	@Input() accept: any
	@Input() maxFileSize: any
	@Input() auto = true
	@Input() withCredentials: any
	@Input() invalidFileSizeMessageSummary: any
	@Input() invalidFileSizeMessageDetail: any
	@Input() invalidFileTypeMessageSummary: any
	@Input() invalidFileTypeMessageDetail: any
	@Input() previewWidth: any
	@Input() chooseLabel = 'Choose'
	@Input() uploadLabel = 'Upload'
	@Input() cancelLabel = 'Cancel'
	@Input() customUpload: any
	@Input() showUploadButton: any
	@Input() showCancelButton: any
	@Input() dataUriPrefix: any
	@Input() deleteButtonLabel: any
	@Input() deleteButtonIcon = 'close'
	@Input() showUploadInfo: any

	@ViewChild('fileUpload') fileUpload: ElementRef | undefined

	inputFileName: string = ""

	@Input() files: File[] = []

	@Output() onFileSelectedEmitter: EventEmitter<any> = new EventEmitter();
	@Output() onFileRemovedEmitter: EventEmitter<any> = new EventEmitter();

	constructor(private sanitizer: DomSanitizer) {

	}

	onClick(event: any) {
		if (this.fileUpload)
			this.fileUpload.nativeElement.click()
	}

	onInput(event: any) {

	}

	onFileSelected(event: any) {
		let files = event.dataTransfer ? event.dataTransfer.files : event.target.files;
		for (let i = 0; i < files.length; i++) {
			let file = files[i];

			if (this.validate(file)) {
				file.objectURL = this.sanitizer.bypassSecurityTrustUrl((window.URL.createObjectURL(files[i])));
				if (!this.isMultiple()) this.files = []
				this.files.push(files[i])
			}
		}

		this.onFileSelectedEmitter.emit(this.files)
	}

	removeFile(event: any, file: File) {
		let ix
		if (this.files && -1 !== (ix = this.files.indexOf(file))) {
			this.files.splice(ix, 1);
			this.clearInputElement();
			this.onFileRemovedEmitter.emit(file);
		}
	}

	validate(file: File) {
		for (const f of this.files) {
			if (f.name === file.name
				&& f.lastModified === file.lastModified
				&& f.size === f.size
				&& f.type === f.type
			) {
				return false
			}
		}
		return true
	}

	clearInputElement() {
		this.fileUpload!.nativeElement.value = ''
	}


	isMultiple(): boolean {
		return this.multiple
	}

}
