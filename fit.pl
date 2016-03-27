#! /usr/local/bin/perl
#
# Usage: fit dir size
#
use warnings;
use strict;
use File::Find;

my $binsize;
my @files;
my @bins;

# -----------------------------------------------------------------------------
# Convert a number to human readable
#
sub num_to_human {
  my $num = shift;
  my $suffix = "B";

  if ($num > 1024 * 1024) {
    $suffix = "M";
    $num /= 1024 * 1024;
  } elsif ($num > 1024) {
    $suffix = "K";
    $num /= 1024;
  }

  if ($suffix eq "B") { return sprintf("%dB", $num); }
  return sprintf("%.2f$suffix", $num);
}

# -----------------------------------------------------------------------------
# Add a name/size tuple to bin bin
#
sub add {
  my ($bin, $name, $size) = @_;
  if ($size > $bin->{free}) {
    printf("Can't fit %s (%s) into %s\n", $name, num_to_human($size),
      num_to_human($bin->{free}));
    exit(1);
  }
  push(@{$bin->{contents}}, [$name, $size]);
  $bin->{free} -= $size;
  $bin->{items}++;
}

# -----------------------------------------------------------------------------
# Get a bin which fits size or create a new one for it
#
sub getbin {
  my $size = shift;
  foreach my $bin (@bins) {
    if ($size <= $bin->{free}) {
        return $bin;
    }
  }
  push(@bins, { "items"    => 0,
                "free"     => $binsize,
                "contents" => [] });
  return $bins[$#bins];
}

# -----------------------------------------------------------------------------
# Get a list of filenames/sizes from path path
#
sub getfiles {
  my $path = shift;
  find(sub{if (-f) {push(@files, [$File::Find::name, -s]);}}, $path);
  # sort by size so large items come first (pop will take largest first)
  @files = sort { $a->[1] - $b->[1] } @files; 
}

# -----------------------------------------------------------------------------
# Main
#
# - Check arguments
# - Initialise the binsize
# - Find all needed files
# - Fit them into bins
# - Print the results
#
if ($#ARGV != 1) {
  print("usage: fit.pl path size\n");
  exit(1);
}

$binsize = $ARGV[1];
if ($binsize =~ /[gG]$/) {
  $binsize =~ s/[^0-9]//g; 
  $binsize *= 1024 * 1024 * 1024;
} elsif ($binsize =~ /[mM]$/) {
  $binsize =~ s/[^0-9]//g;
  $binsize *= 1024 * 1024;
} elsif ($binsize =~ /[kK]$/) {
  $binsize =~ s/[^0-9]//g;
  $binsize *= 1024;
} else {
  $binsize =~ s/[^0-9]//g;
}

getfiles($ARGV[0]);
while ($#files >= 0) {
  my ($name, $size) = @{pop(@files)};
  add(getbin($size), $name, $size);
}

my $total_wasted = 0;                   
foreach my $bin (@bins) {
  foreach my $tuple (@{$bin->{contents}}) {
    my ($name, $size) = @{$tuple};
    print $name."\n";
  }
  printf("==> %.1f%% wasted (%s)\n\n", $bin->{free}/$binsize * 100.0,
    num_to_human($bin->{free}));
  $total_wasted += $bin->{free};
}

printf("Total %d bins, %.1f%% (%s) wasted\n", $#bins+1,
  $total_wasted/(($#bins+1)*$binsize)*100.0, num_to_human($total_wasted));

