module_mm = 2.5;
thickness = 10;
num_teeth = 60;
dedendum_factor = 1.25;
clearance = 0.2;

addendum = module_mm;
dedendum = module_mm * dedendum_factor;
pitch_diameter = num_teeth * module_mm;
outer_diameter = pitch_diameter + 2 * addendum;
root_diameter = pitch_diameter - 2 * dedendum;
tooth_angle = 360 / num_teeth;

function deg2rad(degrees) = degrees * (PI / 180);

module gear() {
    difference() {
        cylinder(h = thickness, d = outer_diameter, center = true);
        cylinder(h = thickness + 1, d = root_diameter, center = true);
        for (i = [0 : num_teeth - 1]) {
            rotate(i * tooth_angle) {
                translate([pitch_diameter / 2, 0, 0]) {
                    rotate([0, 0, tooth_angle / 2]) {
                        cube([addendum, thickness, thickness], center = true);
                    }
                }
            }
        }
    }
}

gear();