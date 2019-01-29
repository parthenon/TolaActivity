import React from 'react'
import Select from 'react-select'
import { observer } from "mobx-react"

@observer
export default class EditUserProfile extends React.Component {
    constructor(props) {
        super(props)
        const {userData} = props
        const organization_listing = props.organizations.map(org => ({value: org.id, label: org.name}))
        const selected_organization = organization_listing.find(o => o.value == userData.organization_id)
        this.state = {
            original_user_data: {...userData},
            managed_user_data: {...userData},
            selected_organization,
            organization_listing
        }
    }


    save(e) {
        e.preventDefault()
        this.props.onUpdate(this.state.managed_user_data)
    }

    saveNew(e) {
        e.preventDefault()
        this.props.onCreate(this.state.managed_user_data)
    }

    saveNewAndAddAnother(e) {
        e.preventDefault()
        this.props.onCreateAndAddAnother(this.state.managed_user_data)
    }

    updateFullName(new_full_name) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                name: new_full_name,
            }
        })
    }

    updateModeOfAddress(new_mode_of_address) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                mode_of_address: new_mode_of_address,
            }
        })
    }

    updateOrganization(new_option) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                organization_id: new_option.value,
            },
            selected_organization: new_option
        })
    }

    updateTitle(new_title) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                title: new_title,
            }
        })
    }

    updateEmail(new_email) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                user: {
                    ...this.state.managed_user_data.user,
                    email: new_email,
                }
            }
        })
    }

    updatePhone(new_phone) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                phone: new_phone,
            }
        })
    }

    updateModeOfContact(new_mode_of_contact) {
        this.setState({
            managed_user_data: {
                ...this.state.managed_user_data,
                mode_of_contact: new_mode_of_contact,
            }
        })
    }

    resetForm() {
        const selected_organization = this.state.organization_listing.find(o => o.value == this.state.original_user_data.organization_id)
        this.setState({
            managed_user_data: this.state.original_user_data,
            selected_organization
        })
    }

    render() {
        const ud = this.state.managed_user_data
        const e = this.props.errors
        const error_classes = {
            name: (e.name)?'is-invalid':'',
            email: (e.user && e.user.email)?'is-invalid':'',
            organization: (e.organization_id)?'is-invalid':''
        }
        console.log(error_classes)
        return (
            <div className="edit-user-profile container">
                <form className="form">
                    <div className="form-group">
                        <label htmlFor="user-full-name-input">Full name<span className="required">*</span></label>
                        <input
                            className={"form-control "+error_classes.name}
                            type="text"
                            value={ud.name}
                            onChange={(e) => this.updateFullName(e.target.value) }
                            id="user-full-name-input"
                            required />
                        {e.name &&
                        <div className="invalid-feedback">
                            {e.name}
                        </div>
                        }
                    </div>
                    <div className="form-group">
                        <label htmlFor="user-mode-of-address-input">Preferred Mode Of Address</label>
                        <input
                            type="text"
                            value={ud.mode_of_address}
                            onChange={(e) => this.updateModeOfAddress(e.target.value)}
                            className="form-control"
                            id="user-mode-of-address-input" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="user-organization-input">Organization<span className="required">*</span></label>
                        <Select
                            className={"form-control "+error_classes.organization}
                            value={this.state.selected_organization}
                            options={this.state.organization_listing}
                            onChange={(e) => this.updateOrganization(e)}
                            placeholder="None Selected"
                            id="user-organization-input" />
                        {e.organization_id &&
                        <div className="invalid-feedback">
                            {e.organization_id}
                        </div>
                        }
                    </div>
                    <div className="form-group">
                        <label htmlFor="user-title-input">Title</label>
                        <input
                            maxLength="3"
                            type="text"
                            value={ud.title}
                            onChange={(e) => this.updateTitle(e.target.value)}
                            className="form-control"
                            id="user-title-input" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="user-email-input">Email<span className="required">*</span></label>
                        <input
                            className={"form-control "+error_classes.email}
                            type="email"
                            value={ud.user.email}
                            onChange={(e) => this.updateEmail(e.target.value)}
                            id="user-email-input" />
                        {e.user && e.user.email &&
                        <div className="invalid-feedback">
                            {e.user.email}
                        </div>
                        }
                    </div>
                    <div className="form-group">
                        <label htmlFor="user-phone-input">Phone</label>
                        <input
                            type="tel"
                            value={ud.phone}
                            onChange={(e) => this.updatePhone(e.target.value)}
                            className="form-control"
                            id="user-phone-input" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="user-mode-of-contact-input">Preferred Mode of Contact</label>
                        <input
                            type="text"
                            value={ud.mode_of_contact}
                            onChange={(e) => this.updateModeOfContact(e.target.value)}
                            className="form-control"
                            id="user-mode-of-contact-input" />
                    </div>
                    {this.props.new &&
                    <div className="form-group">
                        <button className="btn btn-primary" onClick={(e) => this.saveNew(e)}>Save</button>
                        <button className="btn btn-primary" onClick={(e) => this.saveNewAndAddAnother(e)}>Save And Add Another</button>
                        <button className="btn btn-outline-primary" type="button" onClick={() => this.resetForm()}>Reset</button>
                    </div>
                    }
                    {!this.props.new &&
                    <div className="form-group">
                        <button className="btn btn-primary" onClick={(e) => this.save(e)}>Save</button>
                        <button className="btn btn-outline-primary" type="button" onClick={() => this.resetForm()}>Reset</button>
                    </div>
                    }
                </form>
            </div>
        )
    }
}