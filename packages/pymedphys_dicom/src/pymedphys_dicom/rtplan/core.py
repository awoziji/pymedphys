# Copyright (C) 2019 Cancer Care Associates

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version (the "AGPL-3.0+").

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License and the additional terms for more
# details.

# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# ADDITIONAL TERMS are also included as allowed by Section 7 of the GNU
# Affero General Public License. These additional terms are Sections 1, 5,
# 6, 7, 8, and 9 from the Apache License, Version 2.0 (the "Apache-2.0")
# where all references to the definition "License" are instead defined to
# mean the AGPL-3.0+.

# You should have received a copy of the Apache-2.0 along with this
# program. If not, see <http://www.apache.org/licenses/LICENSE-2.0>.


from collections import namedtuple

import pydicom

from pymedphys_utilities.transforms import convert_IEC_angle_to_bipolar


Point = namedtuple("Point", ("x", "y", "z"))


def get_surface_entry_point(plan: pydicom.Dataset) -> Point:
    """
    Parameters
    ----------
    plan : pydicom.Dataset


    Returns
    -------
    surface_entry_point : Point("x", "y", "z")
        Patient surface entry point coordinates (x,y,z) in the
        Patient-Based Coordinate System described in
        Section C.7.6.2.1.1 [1]_ (mm).


    References
    ----------
    .. [1] https://dicom.innolitics.com/ciods/rt-plan/rt-beams/300a00b0/300a0111/300a012e
    """
    all_surface_entry_points = set()

    # Once we have DicomCollection sorted out, it will likely be worthwhile
    # having this function take a beam sequence parameter, and get the entry
    # point for a given beam sequence
    for beam in plan.BeamSequence:
        for control_point in beam.ControlPointSequence:
            try:
                surface_entry_point = control_point.SurfaceEntryPoint
            except AttributeError:
                pass

            surface_entry_point = tuple(
                float(item) for item in tuple(surface_entry_point)
            )

            all_surface_entry_points.add(surface_entry_point)

    if not all_surface_entry_points:
        raise ValueError("No surface entry point found")

    if len(all_surface_entry_points) > 1:
        raise ValueError("More than one disagreeing surface entry point found")

    surface_entry_point = Point(*all_surface_entry_points.pop())

    return surface_entry_point


def get_metersets_from_dicom(dicom_dataset, fraction_group):
    fraction_group_sequence = dicom_dataset.FractionGroupSequence

    fraction_group_numbers = [
        fraction_group.FractionGroupNumber
        for fraction_group in fraction_group_sequence
    ]

    fraction_group_index = fraction_group_numbers.index(fraction_group)
    fraction_group = fraction_group_sequence[fraction_group_index]

    beam_metersets = tuple(
        float(referenced_beam.BeamMeterset)
        for referenced_beam in fraction_group.ReferencedBeamSequence
    )

    return beam_metersets


def get_gantry_angles_from_dicom(dicom_dataset):
    gantry_angles = [
        set(convert_IEC_angle_to_bipolar([
            control_point.GantryAngle
            for control_point in beam_sequence.ControlPointSequence
        ]))
        for beam_sequence in dicom_dataset.BeamSequence
    ]

    for gantry_angle_set in gantry_angles:
        if len(gantry_angle_set) != 1:
            raise ValueError(
                "Only a single gantry angle per beam is currently supported")

    result = tuple(
        list(item)[0]
        for item in gantry_angles
    )

    return result


def get_fraction_group_index(dicom_dataset, fraction_group_number):
    fraction_group_numbers = [
        fraction_group.FractionGroupNumber
        for fraction_group in dicom_dataset.FractionGroupSequence
    ]

    return fraction_group_numbers.index(fraction_group_number)


def get_referenced_beam_sequence(dicom_dataset, fraction_group_number):
    fraction_group_index = get_fraction_group_index(
        dicom_dataset, fraction_group_number)

    fraction_group = dicom_dataset.FractionGroupSequence[fraction_group_index]
    referenced_beam_sequence = fraction_group.ReferencedBeamSequence

    beam_numbers = [
        referenced_beam.ReferencedBeamNumber
        for referenced_beam in referenced_beam_sequence
    ]

    return beam_numbers, referenced_beam_sequence


def get_beam_indices_of_fraction_group(dicom_dataset, fraction_group_number):
    beam_numbers, _ = get_referenced_beam_sequence(
        dicom_dataset, fraction_group_number)

    beam_sequence_numbers = [
        beam_sequence.BeamNumber
        for beam_sequence in dicom_dataset.BeamSequence
    ]

    beam_indexes = [
        beam_sequence_numbers.index(beam_number)
        for beam_number in beam_numbers
    ]

    return beam_indexes


def get_fraction_group_beam_sequence_and_meterset(dicom_dataset,
                                                  fraction_group_number):
    beam_numbers, referenced_beam_sequence = get_referenced_beam_sequence(
        dicom_dataset, fraction_group_number)

    metersets = [
        referenced_beam.BeamMeterset
        for referenced_beam in referenced_beam_sequence
    ]

    beam_sequence_number_mapping = {
        beam.BeamNumber: beam
        for beam in dicom_dataset.BeamSequence
    }

    beam_sequence = [
        beam_sequence_number_mapping[beam_number]
        for beam_number in beam_numbers
    ]

    return beam_sequence, metersets
