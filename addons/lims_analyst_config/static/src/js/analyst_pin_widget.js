/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2oneField } from "@web/views/fields/many2one/many2one_field";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class AnalystPinField extends Many2oneField {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
    }

    async onSelectionChanged(value) {
        if (value && value[0]) {
            const analystId = value[0];
            const pinVerified = await this.verifyAnalystPin(analystId, value[1]);
            
            if (pinVerified) {
                super.onSelectionChanged(value);
            } else {
                // No actualizar el campo si la verificación falla
                this.notification.add("Verificación de PIN cancelada", {
                    type: "warning"
                });
            }
        } else {
            super.onSelectionChanged(value);
        }
    }

    async verifyAnalystPin(analystId, analystName) {
        return new Promise((resolve) => {
            this.dialog.add(PinVerificationDialog, {
                analystId: analystId,
                analystName: analystName,
                onConfirm: async (pin) => {
                    try {
                        const result = await this.rpc("/web/dataset/call_kw", {
                            model: "lims.analyst",
                            method: "verify_analyst_pin",
                            args: [analystId, pin],
                            kwargs: {}
                        });

                        if (result.success) {
                            this.notification.add(`Verificación exitosa: ${result.analyst_name}`, {
                                type: "success"
                            });
                            resolve(true);
                        } else {
                            this.notification.add(result.message, {
                                type: "danger"
                            });
                            resolve(false);
                        }
                    } catch (error) {
                        this.notification.add("Error en la verificación del PIN", {
                            type: "danger"
                        });
                        resolve(false);
                    }
                },
                onCancel: () => {
                    resolve(false);
                }
            });
        });
    }
}

class PinVerificationDialog extends Component {
    static template = "lims_analyst_config.PinVerificationDialog";
    static props = {
        analystId: Number,
        analystName: String,
        onConfirm: Function,
        onCancel: Function,
        close: Function,
    };

    setup() {
        this.state = {
            pin: "",
            isSubmitting: false
        };
    }

    onPinInput(event) {
        this.state.pin = event.target.value;
    }

    onKeyDown(event) {
        if (event.key === "Enter") {
            this.onConfirm();
        } else if (event.key === "Escape") {
            this.onCancel();
        }
    }

    async onConfirm() {
        if (!this.state.pin || this.state.pin.length < 4) {
            return;
        }

        this.state.isSubmitting = true;
        await this.props.onConfirm(this.state.pin);
        this.props.close();
    }

    onCancel() {
        this.props.onCancel();
        this.props.close();
    }
}

registry.category("fields").add("analyst_pin_selector", AnalystPinField);