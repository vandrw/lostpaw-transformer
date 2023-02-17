<script lang="ts">

import axios, { type AxiosProgressEvent } from "axios";
import { useAlertStore } from "@/stores";

export default {
    data() {
        return {
            dragAndDropCapable: false,
            files: [] as Array<File>,
            uploadPercentage: [] as Array<number>,
            uploadStatus: [] as Array<string>,
        };
    },

    mounted() {
        // Determine if drag and drop functionality is capable in the browser
        this.dragAndDropCapable = this.determineDragAndDropCapable();

        // If drag and drop capable, then we continue to bind events to our elements.
        if (this.dragAndDropCapable) {
            this.bindEvents();
        }
    },

    methods: {
        // Listen to all of the drag events and bind an event listener to each
        // for the fileform.
        bindEvents() {
            [
                "drag",
                "dragstart",
                "dragend",
                "dragover",
                "dragenter",
                "dragleave",
                "drop",
            ].forEach(
                // For each event add an event listener that prevents the default action
                // (opening the file in the browser) and stop the propagation of the event (so
                // no other elements open the file in the browser)
                function (evt: any) {
                    document.getElementById("drop-form-instant")?.addEventListener(
                        evt,
                        (e: { preventDefault: () => void; stopPropagation: () => void; }) => {
                            e.preventDefault();
                            e.stopPropagation();
                        },
                        false
                    );
                }.bind(this)
            );
        },

        determineDragAndDropCapable() {
            // Create a test element to see if certain events
            // are present that let us do drag and drop.
            var div = document.createElement("div");

            /*
            Check to see if the `draggable` event is in the element
            or the `ondragstart` and `ondrop` events are in the element. If
            they are, then we have what we need for dragging and dropping files.

            We also check to see if the window has `FormData` and `FileReader` objects
            present so we can do our AJAX uploading
            */
            return (
                ("draggable" in div || ("ondragstart" in div && "ondrop" in div)) &&
                "FormData" in window &&
                "FileReader" in window
            );
        },

        async handleFileDrop(event: DragEvent) {
            if (event.dataTransfer) {
                // Get the files from the event
                const files = event.dataTransfer.files;

                await this.submitFiles(files);
            }
        },

        async handleFileSelect($event: Event) {
            if ($event.target) {
                // Get the files from the event
                const files = ($event.target as HTMLInputElement).files;

                await this.submitFiles(files);
            }

        },

        selectFiles(event: Event) {
            event.preventDefault();
            let fileInputElement = this.$refs.fileUpload as HTMLInputElement;
            fileInputElement.click()
        },

        async submitFiles(files: FileList | null) {
            const alertStore = useAlertStore();

            // If there are files, then we continue
            if (files) {
                // Loop through the files
                for (let i = 0; i < files.length; i++) {
                    // Check if the files are images
                    if (!files[i].type.match("image.*")) {
                        alertStore.error("Only image files are allowed!");
                        return;
                    }

                    // Add the file to the files array
                    this.files.push(files[i]);
                    this.uploadPercentage.push(0);
                    this.uploadStatus.push("Waiting");
                }
            } else {
                return;
            }

            for (let i = 0; i < this.files.length; i++) {
                const buffer = await this.files[i].arrayBuffer();

                this.uploadStatus[i] = "Uploading";

                try {
                    const response = await axios.post("/api/v1/pet-spotted", buffer, {
                        headers: {
                            // "Authorization": `Bearer ${token}`,
                            "Content-Type": "application/octet-stream",
                        },
                        params: {
                            lat: 0, // TODO: Get lat and lon from image or user
                            lon: 0,
                        },
                        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
                            this.uploadPercentage[i] = Math.round((progressEvent.loaded / progressEvent.total!) * 100);
                        },
                    })

                    this.uploadStatus[i] = "Done!";
                    alertStore.success("File(s) uploaded successfully!");

                    const pet_result = {
                        "pet_image": this.files[i],
                        "compared_pets": response.data,
                    }
                    this.$emit("petResults", pet_result);
                } catch (e: any) {
                    this.uploadStatus[i] = "Fail!";
                    alertStore.error("Could not upload one or more files: " + e.message);
                    this.$emit("filesUploaded");
                }
            }


            // Clear the files array
            this.files = [];
        },
    },
};
</script>

<style scoped>
form {
    display: block;
    height: 400px;
    width: 400px;
    background: #ccc;
    margin: auto;
    margin-top: 40px;
    text-align: center;
    line-height: 400px;
    border-radius: 4px;
}

progress {
    width: 100%;
    margin: auto;
    display: block;
    margin-top: 20px;
    margin-bottom: 20px;
}

progress[value] {
    /* Reset the default appearance */
    -webkit-appearance: none;
    appearance: none;

    width: 100%;
    height: 20px;
}

progress[value]::-webkit-progress-bar {
    background-color: #eee;
    border-radius: 2px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25) inset;
}

progress[value]::-webkit-progress-value {
    background-color: #09ad7f;
    border-radius: 2px;
    transition: width 0.2s ease-in;
}

progress[value]::-moz-progress-bar {
    background-color: #09ad7f;
    border-radius: 2px;
    transition: width 0.2s ease-in;
}

.file-upload-info {
    display: block;
    margin: auto;
    margin-top: 20px;
    margin-bottom: 20px;
    width: 60%;
}

#file-drag-drop-instant {
    display: block;
    margin: auto;
    width: 40vw;
}
</style>

<template>
    <div id="file-drag-drop-instant">
        <h2>Upload a picture of a pet</h2>
        <hr />
        <span v-if="!dragAndDropCapable" class="center-span">Drag and drop is not supported by your browser.</span>
        <form v-if="!files.length" id="drop-form-instant" @drop="handleFileDrop($event)">
            <span class="drop-files">
                Drop the files here, or
                <input ref="fileUpload" type="file" multiple hidden @change="handleFileSelect">
                <button class="btn btn-info" @click="selectFiles">Select files</button>
            </span>
        </form>
        <div v-for="(file, index) in files" :key="index">
            <div class="file-upload-info">
                <div>
                    <span style="display: inline-block">{{ file.name }}</span>
                    <span style="float: right;">{{ uploadStatus[index] }}</span>
                </div>
                <progress :value="uploadPercentage[index]" max=100></progress>
            </div>
        </div>
    </div>
</template>